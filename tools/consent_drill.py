"""Fire drill for the proof of consent: change a consent in the ledger, and see it caught.

  python tools/consent_drill.py --customer C-TEST-0001 --profile dpdp-workload-eng \
      --auditor-profile dpdp-workload-auditor

What:        Takes the customer's newest consent and does what someone with write access to the
             ledger could do: replaces its purpose with another. Then:
               1. the proof tool, run with read-only access, must report the record ALTERED,
                  showing the purpose in the ledger and the purpose in the locked copy;
               2. the ledger row is put back, and the proof must be VERIFIED again;
               3. deleting the locked copy must be refused.
             It prints each step on a short line.
Why:         DPDP Act, Section 6(10): the company must be able to prove each consent. A proof is
             trusted once it has been seen to catch a change, the same reasoning as the fire
             drills of Releases 2 and 3. The ledger is an ordinary table that engineers can
             write to; the locked copy is what makes a change visible.
Who runs it: An engineer (PlatformEngineer) for the change; the Auditor profile reads the proof.
             Test T19 runs the same steps and records the evidence.
When:        Release 4, Step 6; again whenever the consent service changes.
Reads:       The ledger, the records bucket and the notices bucket.
Writes:      Nothing on the laptop.
Changes AWS: For a few seconds: one ledger row is changed and then put back exactly as it was.
             The attempt to delete the locked copy is refused, so nothing is removed. If a run
             is interrupted after the change, run it again: it first puts the row back to the
             purpose in the locked copy.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import consent_proof  # noqa: E402

REGION = "ap-south-1"
DENIED = {"AccessDenied", "AccessDeniedException"}


def newest_consent(session, customer: str) -> dict:
    rows = [r for r in consent_proof.ledger_rows(session, customer)
            if r.get("record_type") == "consent"]
    if not rows:
        raise SystemExit(f"No consent recorded for {customer}. Give one first (Release 4, Step 5).")
    return rows[-1]


def status_of(session, customer: str, receipt_key: str) -> dict:
    """The proof result for one record, found by its locked copy (one per purpose)."""
    proof = consent_proof.verify(session, customer)
    return next((r for r in proof["records"] if r.get("receipt_key") == receipt_key), {})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--customer", default="C-TEST-0001")
    ap.add_argument("--profile", required=True, help="engineer profile, to change the ledger")
    ap.add_argument("--auditor-profile", help="read-only profile for the proof (default: --profile)")
    args = ap.parse_args(argv)

    import boto3
    from botocore.exceptions import ClientError
    eng = boto3.Session(profile_name=args.profile, region_name=REGION)
    auditor = boto3.Session(profile_name=args.auditor_profile or args.profile, region_name=REGION)

    row = newest_consent(eng, args.customer)
    receipt = row["receipt_key"]
    s3 = eng.client("s3")
    bucket = consent_proof.names(eng)[0]
    # The true purpose is the one in the locked copy, not the one in the ledger row: if an
    # earlier drill was interrupted between the change and the restore, the row is put right.
    copy = json.loads(s3.get_object(Bucket=bucket, Key=receipt,
                                    VersionId=row["receipt_version_id"])["Body"].read())
    original = copy["purpose_id"]
    other = "credit-check" if original != "credit-check" else "marketing-offers"
    table = eng.resource("dynamodb").Table(consent_proof.LEDGER)
    key = {"customer_id": args.customer, "record_key": row["record_key"]}

    def set_purpose(value):
        table.update_item(Key=key, UpdateExpression="SET purpose_id = :p",
                          ExpressionAttributeValues={":p": value})

    if row["purpose_id"] != original:
        set_purpose(original)
        print("Put back the row of an earlier drill that did not finish.")

    print(f"Consent of {args.customer} to {original}")
    print(f"1. Ledger changed to: {other}")
    set_purpose(other)
    try:
        r = status_of(auditor, args.customer, receipt)
        detected = r.get("status") == "ALTERED"
        print(f"   Proof: {r.get('status')}")
        for field, ledger, locked in r.get("diffs", [])[:1]:
            print(f"   ledger:      {ledger}")
            print(f"   locked copy: {locked}")
    finally:
        set_purpose(original)
    r = status_of(auditor, args.customer, receipt)
    print(f"2. Ledger put back. Proof: {r.get('status')}")
    try:
        s3.delete_object(Bucket=bucket, Key=row["receipt_key"], VersionId=row["receipt_version_id"])
        print("3. Delete locked copy: SUCCEEDED (it should have been refused)")
        refused = False
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        print(f"3. Delete locked copy: refused, {code}")
        refused = code in DENIED
    lock = r.get("lock") or {}
    if lock:
        print(f"   Locked ({lock.get('mode')}) until {lock.get('until')}")
    ok = detected and r.get("status") == "VERIFIED" and refused
    print("Result: " + ("PASS, the change was caught and the proof holds" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
