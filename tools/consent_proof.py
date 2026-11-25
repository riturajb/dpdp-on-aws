"""Prove, for one customer, which notice she was given and which consents she gave.

  python tools/consent_proof.py --customer C-TEST-0001 --profile dpdp-workload-auditor
  python tools/consent_proof.py --customer C-TEST-0001 --profile ... --compact   # short lines
  python tools/consent_proof.py --customer C-TEST-0001 --profile ... --json

What:        Reads the customer's rows in the consent ledger and, for each row, the locked copy
             it points to. It checks four things for every record:
               1. the locked copy exists, in the exact version the row names;
               2. its SHA-256 fingerprint is the one the row recorded;
               3. every field of the row (purpose, notice version, time, how consent was given)
                  is the same as in the locked copy;
               4. the notice version it cites exists, unchanged (its fingerprint matches), so
                  the exact text the person was shown can be produced;
             and reports how long the locked copy is protected, and in which lock mode. It also
             lists any locked copy for the customer that the ledger does not mention.
             Each record ends VERIFIED, ALTERED or MISSING.
Why:         DPDP Act, Section 6(10): where consent is the basis of processing and a question
             arises in a proceeding, the company must prove that a notice was given and consent
             obtained in line with the Act and the Rules. The locked copy cannot be changed or
             deleted, even by an administrator, so a change made to the ledger afterwards is
             found, not hidden.
Who runs it: Anyone with read-only access: in this project, the Auditor permission set
             (profile dpdp-workload-auditor). It never needs write access. Test T19 runs it.
When:        Release 4, Step 6; whenever the company must show a consent, for example in reply
             to the person or to the Data Protection Board.
Reads:       The consent ledger, the records bucket and the notices bucket.   Writes: nothing.
Changes AWS: No.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services" / "consent"))

import consent_rules as rules  # noqa: E402

REGION = "ap-south-1"
LEDGER = "dpdp-consent-ledger"


def names(session) -> tuple[str, str]:
    """The two buckets, named after the account (terraform/modules/consent-service)."""
    account = session.client("sts").get_caller_identity()["Account"]
    return f"dpdp-consent-records-{account}", f"dpdp-notices-{account}"


def ledger_rows(session, customer: str) -> list[dict]:
    """Every ledger row of one customer, oldest first (the sort key starts with the time)."""
    from boto3.dynamodb.conditions import Key
    table = session.resource("dynamodb").Table(LEDGER)
    # ConsistentRead: the answer includes every write made before the query, including one
    # made a moment ago (a test, or a change being investigated).
    rows, kw = [], {"KeyConditionExpression": Key("customer_id").eq(customer),
                    "ConsistentRead": True}
    while True:
        page = table.query(**kw)
        rows += page["Items"]
        if "LastEvaluatedKey" not in page:
            return rows
        kw["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def locked_copies(s3, bucket: str, customer: str) -> set[tuple[str, str]]:
    """(key, version id) of every locked copy for the customer, in both folders."""
    found = set()
    for folder in ("consents", "notice-deliveries"):
        pages = s3.get_paginator("list_object_versions").paginate(
            Bucket=bucket, Prefix=f"{folder}/{customer}/")
        for page in pages:
            for v in page.get("Versions", []):
                found.add((v["Key"], v["VersionId"]))
    return found


def verify(session, customer: str) -> dict:
    """Check every record of one customer. Returns the results and a summary."""
    s3 = session.client("s3")
    records_bucket, notices_bucket = names(session)
    notice_ok: dict[str, bool] = {}
    results, used = [], set()

    for row in ledger_rows(session, customer):
        key, ver = row.get("receipt_key", ""), row.get("receipt_version_id", "")
        used.add((key, ver))
        res = {"recorded_at": row.get("recorded_at"), "record_type": row.get("record_type"),
               "purpose_id": row.get("purpose_id"), "action": row.get("action"),
               "channel": row.get("channel"), "language": row.get("language"),
               "notice_version": row.get("notice_version"), "receipt_key": key,
               "problems": [], "diffs": []}
        # 1. The exact version of the locked copy that the row names.
        try:
            body = s3.get_object(Bucket=records_bucket, Key=key, VersionId=ver)["Body"].read()
        except Exception as e:  # noqa: BLE001 - any failure to read means no proof
            res["status"] = "MISSING"
            res["problems"].append(f"locked copy not found: {type(e).__name__}")
            results.append(res)
            continue
        copy = json.loads(body)
        # 2. Its fingerprint.
        if rules.fingerprint(copy) != row.get("receipt_sha256"):
            res["problems"].append("fingerprint differs from the one the ledger recorded")
        # 3. Each field of the row against the locked copy.
        for f in rules.MATCHED_FIELDS:
            if str(row.get(f)) != str(copy.get(f)):
                res["diffs"].append((f, str(row.get(f)), str(copy.get(f))))
                res["problems"].append(f"{f}: ledger says '{row.get(f)}', "
                                       f"locked copy says '{copy.get(f)}'")
        # 4. The notice the person was shown, unchanged.
        nv = copy.get("notice_version", "")
        if nv not in notice_ok:
            try:
                notice = json.loads(s3.get_object(
                    Bucket=notices_bucket, Key=f"notices/{nv}/notice.json")["Body"].read())
                notice_ok[nv] = rules.fingerprint(notice) == copy.get("notice_sha256")
            except Exception:  # noqa: BLE001
                notice_ok[nv] = False
        if not notice_ok[nv]:
            res["problems"].append(f"notice {nv} is missing or does not match its fingerprint")
        # How long the copy is protected, and how.
        try:
            ret = s3.get_object_retention(Bucket=records_bucket, Key=key,
                                          VersionId=ver)["Retention"]
            res["lock"] = {"mode": ret["Mode"],
                           "until": ret["RetainUntilDate"].date().isoformat()}
        except Exception:  # noqa: BLE001
            res["lock"] = None
            res["problems"].append("the locked copy has no retention lock")
        # The values proved come from the locked copy, never from the ledger row.
        res.update({k: copy.get(k) for k in ("recorded_at", "purpose_id", "action", "channel",
                                             "language", "notice_version", "request_ref")})
        res["status"] = "ALTERED" if res["problems"] else "VERIFIED"
        results.append(res)

    unlisted = sorted(locked_copies(s3, records_bucket, customer) - used)
    counts = {s: sum(r["status"] == s for r in results) for s in ("VERIFIED", "ALTERED", "MISSING")}
    return {"customer_id": customer, "records": results, "counts": counts,
            "unlisted": [k for k, _ in unlisted],
            "result": "VERIFIED" if results and not unlisted and counts["VERIFIED"] == len(results)
            else ("NO RECORDS" if not results and not unlisted else "PROBLEMS")}


def print_full(proof: dict) -> None:
    print(f"Notice and consent records of {proof['customer_id']} (synthetic data)\n")
    for r in proof["records"]:
        what = "notice delivered" if r["record_type"] == "notice_delivered" else \
            f"consent to {r['purpose_id']}"
        print(f"{r['status']:<9} {r['recorded_at']}  {what}")
        print(f"          notice {r['notice_version']} in '{r['language']}', "
              f"by {r['action']} through {r['channel']}")
        if r.get("lock"):
            print(f"          locked ({r['lock']['mode']}) until {r['lock']['until']}")
        for p in r["problems"]:
            print(f"          PROBLEM: {p}")
    for k in proof["unlisted"]:
        print(f"UNLISTED  {k}: a locked copy the ledger does not list")
    c = proof["counts"]
    print(f"\nResult: {proof['result']} ({c['VERIFIED']} verified, {c['ALTERED']} altered, "
          f"{c['MISSING']} missing, {len(proof['unlisted'])} unlisted)")


def print_compact(proof: dict) -> None:
    """At most 46 characters a line, for the demonstration video."""
    print(f"Records of {proof['customer_id']}")
    for r in proof["records"][-6:]:
        what = "notice" if r["record_type"] == "notice_delivered" else r["purpose_id"]
        at = r["recorded_at"] or ""
        print(f"{r['status']:<9}{what[:20]:<21}{at[5:10]} {at[11:16]}")
        for field, ledger, locked in r["diffs"][:1]:
            print(f"  {field} changed in the ledger")
            print(f"    ledger:      {ledger[:28]}")
            print(f"    locked copy: {locked[:28]}")
        for p in [p for p in r["problems"] if ":" not in p.split(" ")[0]][:1]:
            print(f"  {p[:44]}")
    last = next((r for r in reversed(proof["records"]) if r.get("lock")), None)
    if last:
        print(f"Locked {last['lock']['mode']} until {last['lock']['until']}")
    print(f"Result: {proof['result']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--customer", required=True)
    ap.add_argument("--profile", required=True, help="read-only is enough: dpdp-workload-auditor")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--compact", action="store_true", help="short lines, for narrow screens")
    args = ap.parse_args(argv)
    import boto3
    proof = verify(boto3.Session(profile_name=args.profile, region_name=REGION), args.customer)
    if args.json:
        print(json.dumps(proof, indent=2, default=str))
    elif args.compact:
        print_compact(proof)
    else:
        print_full(proof)
    return 0 if proof["result"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
