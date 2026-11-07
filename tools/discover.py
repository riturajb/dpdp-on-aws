"""Find personal data wherever it is in an AWS account, and compare it with the register.

  python tools/discover.py --profile dpdp-workload-auditor          # scan the account
  python tools/discover.py --offline data/                           # scan local files only

What:        Reads the content of every store in the region, finds Indian identifiers in it,
             and gives each finding a verdict against register/personal-data-register.yaml.
Why:         DPDP Act, section 8(1): the company answers for all the personal data it
             processes, including copies nobody planned. A register is only as good as the
             last time someone checked it against what is really stored.
Who runs it: A person or pipeline with read-only access. In this project: the Auditor
             permission set (profile dpdp-workload-auditor). It never needs write access.
When:        Release 2, Steps 3 and 5; again after any fix, to show the problem is gone.
             A company would run it on a schedule and after each new data flow goes live.
Reads:       S3 objects, DynamoDB items, CloudWatch log events, the register.
Writes:      evidence/discovery/<date>-<time>/ on the laptop: report.md and findings.json,
             masked values only. That folder is ignored by Git.
Changes AWS: No. It makes read calls only (List, Get, Scan, Describe, FilterLogEvents).

Release 1 compared the register with the resources tagged DataClass=personal. Tags show only
what someone remembered to label. This scanner looks at everything it can read in the region:
every S3 bucket, every DynamoDB table and every CloudWatch Logs log group, tagged or not.

Each finding gets one of three verdicts:
  expected               a store in the register, holding the identifier in a field the register lists
  unexpected category    a store in the register, holding an identifier the register does not list there
  unregistered store     a store the register does not know about

The report holds masked values only. It deliberately holds no hashes of identifiers either:
a 12-digit Aadhaar number can be recovered from its hash by trying every possible number.

Not scanned in Release 2: backups and snapshots (Release 8), and objects larger than 5 MB.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import detectors, register  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REGION = "ap-south-1"      # Fernleaf keeps all personal data in Mumbai; other regions are blocked
# Limits that keep a scan of a small account to a few minutes and a few rupees of API calls.
# A company with large buckets would use Amazon Macie for S3 and keep this for tables and logs.
MAX_OBJECT_BYTES = 5 * 1024 * 1024
LOG_DAYS = 14              # debug logs leak data today; two weeks covers recent releases
# Text formats only. Images, PDFs and Parquet files need other tools (see the Release 2 guide).
TEXT_SUFFIXES = (".json", ".jsonl", ".csv", ".txt", ".log", ".json.gz", ".jsonl.gz", ".log.gz", ".csv.gz")

# The field in which the register expects each kind of identifier.
REGISTER_FIELD = {"aadhaar": "aadhaar_number", "pan": "pan", "mobile": "mobile", "email": "email"}


@dataclass
class Finding:
    store_kind: str      # dynamodb_table, s3_bucket, log_group
    store_name: str
    field: str           # attribute, JSON key or CSV column; "(text)" when the value has no field
    identifier: str
    confidence: str
    count: int = 0
    examples: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    verdict: str = ""
    store_id: str = ""
    note: str = ""


class Collector:
    """Gathers matches and groups them by store, field, identifier and confidence."""

    def __init__(self, ignore: set[str]):
        self.ignore = ignore
        self.groups: dict[tuple, Finding] = {}

    def scan(self, kind: str, name: str, fld: str, text: str, location: str) -> None:
        # One finding per store, field, identifier and confidence, with a count. A report that
        # listed every match would be thousands of lines long and nobody would read it.
        for m in detectors.find(text, self.ignore):
            key = (kind, name, fld, m.identifier, m.confidence)
            f = self.groups.setdefault(key, Finding(kind, name, fld, m.identifier, m.confidence))
            f.count += 1
            if len(f.examples) < 3 and m.masked not in f.examples:
                f.examples.append(m.masked)
            if len(f.locations) < 3 and location not in f.locations:
                f.locations.append(location)

    def scan_value(self, kind: str, name: str, fld: str, value, location: str) -> None:
        """Walk a JSON-like value; each string is scanned under the key that holds it."""
        if isinstance(value, dict):
            for k, v in value.items():
                self.scan_value(kind, name, str(k), v, location)
        elif isinstance(value, list):
            for v in value:
                self.scan_value(kind, name, fld, v, location)
        elif value is not None:
            self.scan(kind, name, fld, str(value), location)

    def scan_document(self, kind: str, name: str, text: str, location: str) -> None:
        """Scan a file's text as JSON, JSON lines or CSV where it parses, otherwise as plain text.
        Parsing matters: a PAN under the key "pan" is expected in a loans table, the same PAN
        under "notes" is not. Plain text gives the field "(text)"."""
        stripped = text.strip()
        try:
            self.scan_value(kind, name, "(text)", json.loads(stripped), location)
            return
        except ValueError:
            pass
        lines = stripped.splitlines()
        try:
            for line in lines:
                self.scan_value(kind, name, "(text)", json.loads(line), location)
            return
        except ValueError:
            pass
        if lines and "," in lines[0]:
            reader = csv.DictReader(io.StringIO(stripped))
            if reader.fieldnames and len(reader.fieldnames) > 1:
                for row in reader:
                    for k, v in row.items():
                        self.scan(kind, name, k or "(text)", v or "", location)
                return
        for line in lines:
            self.scan(kind, name, "(text)", line, location)


def scan_account(session) -> tuple[Collector, str]:
    """Read every bucket, table and log group the session can see in the region."""
    account = session.client("sts").get_caller_identity()["Account"]
    # The account id is 12 digits and appears in bucket names; it is not an Aadhaar number.
    col = Collector(ignore={account})

    # S3: every bucket, tagged or not. Tags are what Release 1 relied on; this does not.
    s3 = session.client("s3")
    for b in s3.list_buckets()["Buckets"]:
        name = b["Name"]
        region = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
        if region != REGION:
            continue
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=name):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if obj["Size"] > MAX_OBJECT_BYTES or not key.lower().endswith(TEXT_SUFFIXES):
                    continue
                body = s3.get_object(Bucket=name, Key=key)["Body"].read()
                if key.lower().endswith(".gz"):
                    body = gzip.decompress(body)
                col.scan_document("s3_bucket", name, body.decode("utf-8", errors="replace"), f"s3://{name}/{key}")

    # DynamoDB: every item of every table. Macie does not read DynamoDB at all, which is why
    # this project has its own scanner. A full Scan reads the whole table: fine for small
    # tables; a large table would be exported to S3 first and scanned there.
    ddb = session.client("dynamodb")
    from boto3.dynamodb.types import TypeDeserializer
    plain = TypeDeserializer()
    for page in ddb.get_paginator("list_tables").paginate():
        for table in page["TableNames"]:
            for scan in ddb.get_paginator("scan").paginate(TableName=table):
                for item in scan["Items"]:
                    row = {k: plain.deserialize(v) for k, v in item.items()}
                    ref = row.get("customer_id", "item")
                    col.scan_value("dynamodb_table", table, "(text)", row, f"{table} item {ref}")

    # CloudWatch Logs: the last LOG_DAYS days of every log group. Application logs are where
    # personal data most often leaks without anyone deciding to store it.
    logs = session.client("logs")
    since = int((time.time() - LOG_DAYS * 86400) * 1000)
    for page in logs.get_paginator("describe_log_groups").paginate():
        for group in page["logGroups"]:
            gname = group["logGroupName"]
            for events in logs.get_paginator("filter_log_events").paginate(logGroupName=gname, startTime=since):
                for e in events["events"]:
                    col.scan_document("log_group", gname, e["message"], f"{gname} stream {e['logStreamName']}")
    return col, account


def scan_files(folder: str) -> tuple[Collector, str]:
    """Offline: scan the synthetic data files written by generate_synthetic_data.py.
    Each file stands for the store it is loaded into."""
    col = Collector(ignore=set())
    stores = {"customers": ("dynamodb_table", "dpdp-customers"), "loans": ("dynamodb_table", "dpdp-loans"),
              "wallet": ("dynamodb_table", "dpdp-wallet-transactions"),
              "tickets": ("dynamodb_table", "dpdp-support-tickets"),
              "bureau": ("s3_bucket", "dpdp-bureau-reports-000000000000"),
              "events": ("s3_bucket", "dpdp-app-events-000000000000")}
    for path in sorted(Path(folder).glob("*.json")):
        kind, name = stores.get(path.stem, ("s3_bucket", path.stem))
        col.scan_document(kind, name, path.read_text(), str(path))
    return col, "000000000000"


def reconcile(col: Collector, reg: dict, account: str) -> list[Finding]:
    """Give every finding its verdict by comparing it with the register."""
    names = register.store_names(reg, account)
    by_name = {n: sid for sid, n in names.items()}
    fields_in_store: dict[str, set[str]] = defaultdict(set)
    for c in reg["data_categories"]:
        for sid in c.get("stores", []):
            fields_in_store[sid].update(c.get("fields", []))

    # Three verdicts, in order of seriousness:
    #   unregistered store   the company does not know this store holds personal data at all
    #   unexpected category  the store is known, but this kind of data, or this field, is not
    #   expected             the register already says this data is here
    # "(text)" counts as the expected field for a registered category, because files such
    # as bureau reports hold identifiers in free text by design.
    out = []
    for f in col.groups.values():
        f.store_id = by_name.get(f.store_name, "")
        expected_field = REGISTER_FIELD[f.identifier]
        if not f.store_id:
            f.verdict = "unregistered store"
        elif expected_field in fields_in_store[f.store_id] and f.field in (expected_field, "(text)"):
            f.verdict = "expected"
        else:
            f.verdict = "unexpected category"
        # Aadhaar numbers carry their own rule, whatever the verdict, so the report says so.
        if f.identifier == "aadhaar":
            f.note = ("Full Aadhaar number stored. A lender that authenticates Aadhaar through UIDAI "
                      "must keep Aadhaar numbers in an Aadhaar Data Vault (UIDAI circular of 18 July 2025).")
        out.append(f)
    order = {"unregistered store": 0, "unexpected category": 1, "expected": 2}
    return sorted(out, key=lambda x: (order[x.verdict], x.store_name, x.field, x.identifier))


def report(findings: list[Finding], account: str, source: str) -> str:
    """The report as Markdown: problems first, then what was expected."""
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %B %Y, %H:%M IST")
    problems = [f for f in findings if f.verdict != "expected"]
    lines = [f"# Personal data discovery report", "",
             f"Scanned: {source}, {now}. Values are masked.", "",
             f"Problems: {len(problems)} findings in {len({f.store_name for f in problems})} stores. "
             f"Expected: {len(findings) - len(problems)} findings.", ""]
    for title, wanted in (("Problems", lambda f: f.verdict != "expected"), ("Expected", lambda f: f.verdict == "expected")):
        rows = [f for f in findings if wanted(f)]
        lines += [f"## {title}", ""]
        if not rows:
            lines += ["None.", ""]
            continue
        lines += ["| Verdict | Store | Field | Identifier | Confidence | Count | Examples |",
                  "|---|---|---|---|---|---|---|"]
        for f in rows:
            lines.append(f"| {f.verdict} | {f.store_name} | {f.field} | {f.identifier} | {f.confidence} | "
                         f"{f.count} | {', '.join(f.examples)} |")
        lines.append("")
    notes = sorted({(f.store_name, f.note) for f in findings if f.note})
    if notes:
        lines += ["## Notes", ""] + [f"- {store}: {note}" for store, note in notes] + [""]
    return "\n".join(lines)


def compact(findings: list[Finding], account: str) -> str:
    """Short lines, for narrow screens: problems one per line, then the expected total."""
    def short(name: str) -> str:
        name = name.replace(f"-{account}", "")
        return name[5:] if name.startswith("dpdp-") else name
    problems = [f for f in findings if f.verdict != "expected"]
    word = {"unregistered store": "UNREGISTERED", "unexpected category": "UNEXPECTED"}
    def n(k: int, word: str) -> str:
        return f"{k} {word}" + ("" if k == 1 else "s")
    lines = [f"Problems: {n(len(problems), 'finding')} in {n(len({f.store_name for f in problems}), 'store')}"]
    lines += [f"{word[f.verdict]:<13}{short(f.store_name):<20}{f.identifier} {f.count}" for f in problems]
    expected = [f for f in findings if f.verdict == "expected"]
    lines.append(f"Expected: {n(len(expected), 'finding')} in {n(len({f.store_name for f in expected}), 'store')}")
    return "\n".join(lines)


def save(findings: list[Finding], text: str) -> Path:
    """Keep the report and its findings on the laptop, in evidence/discovery/ (ignored by Git)."""
    stamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d-%H%M%S")
    folder = ROOT / "evidence" / "discovery" / stamp
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "report.md").write_text(text)
    (folder / "findings.json").write_text(json.dumps([f.__dict__ for f in findings], indent=1))
    return folder


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="AWS CLI profile with read access, such as dpdp-workload-auditor")
    ap.add_argument("--offline", metavar="FOLDER", help="scan local synthetic data files instead of AWS")
    ap.add_argument("--compact", action="store_true", help="short lines, for narrow screens")
    args = ap.parse_args(argv)
    if args.offline:
        col, account = scan_files(args.offline)
        source = f"local files in {args.offline}"
    else:
        import boto3
        col, account = scan_account(boto3.Session(profile_name=args.profile, region_name=REGION))
        source = f"AWS account (id masked), {REGION}"
    findings = reconcile(col, register.load(), account)
    text = report(findings, account, source)
    folder = save(findings, text)
    print(compact(findings, account) if args.compact else text)
    if not args.compact:
        print(f"Saved in {folder.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
