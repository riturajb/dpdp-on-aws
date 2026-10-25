"""Show, for one customer, every category of personal data the company holds about her:
where it is stored, why, under which legal basis, who receives it, and until when it is kept.

This is the basis of the summary a company must give on request under Section 11(1).

  python tools/customer_summary.py --customer C-TEST-0001 --profile dpdp-workload-eng
  python tools/customer_summary.py --customer C-TEST-0001 --offline data/     # from generated files
  add --brief for one line per category
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import register  # noqa: E402

# Identifiers are never printed in full.
MASK = {"aadhaar_number": lambda v: "XXXX XXXX " + v[-4:], "pan": lambda v: "XXXXX" + v[5:9] + "X",
        "mobile": lambda v: v[:-4] + "XXXX"}


class OfflineSource:
    """Reads the files written by generate_synthetic_data.py."""

    def __init__(self, folder: str):
        f = Path(folder)
        self.d = {n: json.loads((f / f"{n}.json").read_text()) for n in
                  ("customers", "loans", "wallet", "tickets", "bureau", "events")}

    def records(self, store: str, cid: str) -> list[dict]:
        if store == "customers-db":
            return [c for c in self.d["customers"] if c["customer_id"] == cid]
        if store == "loans-db":
            return [x for x in self.d["loans"] if x["customer_id"] == cid]
        if store == "wallet-db":
            return [x for x in self.d["wallet"] if x["customer_id"] == cid]
        if store == "tickets-db":
            return [x for x in self.d["tickets"] if x["customer_id"] == cid]
        if store == "bureau-reports":
            return [self.d["bureau"][cid]] if cid in self.d["bureau"] else []
        if store == "app-events":
            return self.d["events"].get(cid, [])
        return []


class LiveSource:
    """Reads the stores in an AWS account."""

    def __init__(self, session, reg: dict):
        account = session.client("sts").get_caller_identity()["Account"]
        self.names = register.store_names(reg, account)
        self.types = {s["id"]: s["type"] for s in reg["stores"]}
        self.dynamo = session.resource("dynamodb")
        self.s3 = session.client("s3")

    def records(self, store: str, cid: str) -> list[dict]:
        from boto3.dynamodb.conditions import Key
        name = self.names[store]
        if self.types[store] == "dynamodb_table":
            return self.dynamo.Table(name).query(KeyConditionExpression=Key("customer_id").eq(cid))["Items"]
        key = {"bureau-reports": f"bureau/{cid}.json", "app-events": f"events/{cid}.jsonl"}[store]
        try:
            body = self.s3.get_object(Bucket=name, Key=key)["Body"].read().decode()
        except self.s3.exceptions.NoSuchKey:
            return []
        return [json.loads(line) for line in body.splitlines() if line.strip()]


def kept_until(retention: dict, customer: dict, records: list[dict]) -> str:
    """Turn the register's retention rule into a plain-English date or period for this customer."""
    rule = retention["rule"]
    note = "" if retention.get("confirmed") else " (period to be confirmed)"
    if rule == "until_withdrawn":
        return "Until consent is withdrawn, then erased"
    if rule == "after_account_closure":
        years = round(retention["days"] / 365.25, 1)
        span = f"{int(years)} years" if years >= 1.5 else f"{retention['days']} days"
        if customer.get("closed_on"):
            end = date.fromisoformat(customer["closed_on"]) + timedelta(days=retention["days"])
            return f"{end.isoformat()} ({span} after the account closed){note}"
        return f"While the account is open, then {span} after it closes{note}"
    if rule == "after_record":
        field = retention["date_field"]
        dates = sorted(str(r[field])[:10] for r in records if r.get(field))
        if not dates:
            return "No records"
        first = date.fromisoformat(dates[0]) + timedelta(days=retention["days"])
        last = date.fromisoformat(dates[-1]) + timedelta(days=retention["days"])
        return f"Each record for {retention['days']} days: oldest until {first}, newest until {last}{note}"
    return "Unknown rule"


def summarise(reg: dict, source, cid: str) -> list[dict]:
    """For each register category, find the customer's records in its stores. A category is listed
    only if at least one of its fields is present, so the summary shows what is actually held."""
    vendors = {v["id"]: v for v in reg["vendors"]}
    cache = {}
    customer = (source.records("customers-db", cid) or [{}])[0]
    if not customer:
        raise SystemExit(f"No customer {cid} found.")
    out = []
    for c in reg["data_categories"]:
        held, fields = [], set()
        for s in c["stores"]:
            rows = cache.setdefault(s, source.records(s, cid))
            present = {f for r in rows for f in c["fields"] if r.get(f) not in (None, "", [])}
            if present:
                held.append(s)
                fields |= present
        if not held:
            continue
        rows = [r for s in held for r in cache[s]]
        sample = {f: next((r[f] for r in rows if r.get(f) not in (None, "")), None) for f in fields}
        shown = [f"{f} ({MASK[f](str(sample[f]))})" if f in MASK and sample[f] else f for f in c["fields"] if f in fields]
        out.append({
            "category": c["name"], "stores": held, "fields": shown,
            "purposes": [{"purpose": p["purpose"], "legal_basis": register.BASIS_LABEL.get(p.get("legal_basis"), "NONE"),
                          "shared_with": [f"{vendors[v]['name']} ({vendors[v]['location']})" for v in p.get("shared_with") or []]}
                         for p in c["purposes"]],
            "kept_until": kept_until(c["retention"], customer, rows),
            "records": len(rows),
        })
    return out


SHORT_CATEGORY = {
    "Marketing preferences": "Marketing choices",
    "Repayments and collections": "Repayments",
    "Credit bureau report": "Bureau report",
    "Wallet transactions": "Wallet payments",
    "App and device activity": "App activity",
    "Complaints and support requests": "Complaints",
}


def _basis_short(b: str) -> str:
    if b.startswith("Consent"):
        return "Consent"
    m = re.search(r"Section 7\((\w+)\)", b)
    return f"Sec 7({m.group(1)})" if m else b[:9]


def _kept_short(k: str) -> str:
    m = re.search(r"then (\d+) years after it closes", k)
    if m:
        return f"{m.group(1)} yrs*"
    m = re.search(r"then (\d+) days after it closes", k)
    if m:
        return "1 yr*" if m.group(1) == "365" else f"{m.group(1)} days*"
    if k.startswith("Until consent is withdrawn"):
        return "until withdrawn"
    m = re.search(r"Each record for (\d+) days", k)
    return f"{m.group(1)} days" if m else k[:15]


def compact(rows: list[dict], cid: str) -> list[str]:
    """At most 46 characters per line, for a phone screen: category, legal basis, how long it is kept,
    and the masked Aadhaar and PAN as they are held."""
    out = [f"Customer {cid} (synthetic data)", "", f"{'Category':<20}{'Basis':<10}Kept"]
    ids = []
    for r in rows:
        out.append(f"{SHORT_CATEGORY.get(r['category'], r['category'])[:19]:<20}"
                   f"{_basis_short(r['purposes'][0]['legal_basis']):<10}{_kept_short(r['kept_until'])}")
        ids += [f.split(" (")[1].rstrip(")") for f in r["fields"] if f.startswith(("aadhaar", "pan")) and " (" in f]
    stores = {s for r in rows for s in r["stores"]}
    out += ["", f"{len(rows)} categories in {len(stores)} stores"]
    if ids:
        out.append("Aadhaar " + ids[0] + (", PAN " + ids[1] if len(ids) > 1 else ""))
    out.append("* after the account closes")
    return out


def main(argv=None) -> int:
    """Command line: full view, --brief (one line per category), --compact (phone width) or --json."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--customer", required=True)
    ap.add_argument("--profile")
    ap.add_argument("--offline", help="folder written by generate_synthetic_data.py")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--brief", action="store_true", help="one line per category")
    ap.add_argument("--compact", action="store_true", help="short lines, for the demonstration video")
    args = ap.parse_args(argv)
    reg = register.load()
    if args.offline:
        source = OfflineSource(args.offline)
    else:
        import boto3
        source = LiveSource(boto3.Session(profile_name=args.profile, region_name="ap-south-1"), reg)
    rows = summarise(reg, source, args.customer)
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    if args.compact:
        print("\n".join(compact(rows, args.customer)))
        return 0
    print(f"Personal data held about customer {args.customer} (synthetic data)\n")
    if args.brief:
        w = max(len(r["category"]) for r in rows)
        for r in rows:
            p = r["purposes"][0]
            vendors = ", ".join(v.split(" (")[0] for v in p["shared_with"]) or "nobody"
            print(f"  {r['category']:<{w}}  | {p['legal_basis']:<32} | shared with: {vendors}")
            print(f"  {'':<{w}}  | held in: {', '.join(r['stores'])} | kept: {r['kept_until']}")
        print(f"\n{len(rows)} categories of personal data.")
        return 0
    for r in rows:
        print(f"{r['category']}")
        n = r["records"]
        plural = "" if n == 1 else "s"
        print(f"  Held in      : {', '.join(r['stores'])}  ({n} record{plural})")
        print(f"  Fields       : {', '.join(r['fields'])}")
        for p in r["purposes"]:
            print(f"  Purpose      : {p['purpose']}")
            print(f"  Legal basis  : {p['legal_basis']}")
            print(f"  Shared with  : {', '.join(p['shared_with']) or 'Nobody outside the company'}")
        print(f"  Kept until   : {r['kept_until']}\n")
    print(f"{len(rows)} categories of personal data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
