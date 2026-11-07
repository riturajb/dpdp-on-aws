"""Fire drill: plant three realistic personal data problems, so the scanner has something to find.

  python tools/plant_findings.py --profile dpdp-workload-eng            # plant all three
  python tools/plant_findings.py --profile dpdp-workload-eng --remove   # remove all three

What:        Creates three known problems in the account, and removes them again.
Why:         A detection control is only trusted once it has been seen to catch something.
             Auditors ask for exactly this: plant a known case, show it is caught, keep the
             evidence. Without it, "the scan found nothing" could mean the scanner is broken.
Who runs it: An engineer with write access (PlatformEngineer, profile dpdp-workload-eng).
             The scan that follows uses a different, read-only identity, as it would in a
             company where the person who tests a control is not the person who owns it.
When:        Release 2, Step 4 (plant) and Step 7 (remove). Run it again whenever the scanner
             changes, to show it still catches all three.
Reads:       The register (store names) and the synthetic customers.
Writes:      AWS only, see below. Nothing on the laptop.
Changes AWS: Yes. One DynamoDB item, one S3 bucket with one object, one log group.
             Undo: --remove deletes all three. Running plant twice is safe.

All values come from the synthetic customers (same seed as generate_synthetic_data.py), so
nothing here can belong to a real person. The three problems are ones Indian lenders meet:

  1. A collections agent types a customer's full Aadhaar number into the notes of a support
     ticket while verifying the customer on a call. The tickets table is in the register, but
     the register does not list Aadhaar numbers there.
  2. The marketing team exports names, mobile numbers and email addresses to a CSV file in a
     new bucket, for a campaign. Nobody tags the bucket or adds it to the register.
  3. The loan application service writes full request bodies, with PAN and mobile number, into
     its debug log. Nobody planned for personal data in that log.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import generate_synthetic_data, register  # noqa: E402

REGION = "ap-south-1"
TICKET_ID_SUFFIX = "-002"
LOG_GROUP = "/fernleaf/loan-api"
LOG_STREAM = "debug"
EXPORT_KEY = "campaigns/diwali-offer-leads.csv"


def export_bucket(account: str) -> str:
    return f"dpdp-marketing-export-{account}"


# Customers with an Aadhaar number, other than C-TEST-0001, which Release 1 uses for its own
# tests. Each problem uses different customers, so the findings cannot be confused.
def _adults(data: dict) -> list[dict]:
    return [c for c in data["customers"] if c.get("aadhaar_number") and c["customer_id"] != "C-TEST-0001"]


def plant(session) -> list[str]:
    account = session.client("sts").get_caller_identity()["Account"]
    names = register.store_names(register.load(), account)
    data = generate_synthetic_data.build(200, 2026)   # same seed as Release 1: same customers
    adults = _adults(data)
    done = []

    # 1. Aadhaar typed into ticket notes.
    c = adults[0]
    a = c["aadhaar_number"]
    session.resource("dynamodb").Table(names["tickets-db"]).put_item(Item={
        "customer_id": c["customer_id"], "ticket_id": f"S-{c['customer_id']}{TICKET_ID_SUFFIX}",
        "channel": "phone", "created_at": "2026-10-30",
        "text": f"Collections call. Customer confirmed identity by reading out Aadhaar {a[:4]} {a[4:8]} {a[8:]}. "
                "Promised to pay the overdue instalment on Friday."})
    done.append(f"Ticket S-{c['customer_id']}{TICKET_ID_SUFFIX} with an Aadhaar number in its notes")

    # 2. Marketing export in a bucket nobody tagged. Bucket names are global, so the account
    #    id is part of the name. No DataClass tag: the Release 1 tag check cannot see it.
    s3 = session.client("s3")
    bucket = export_bucket(account)
    try:
        s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": REGION})
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["full_name", "mobile", "email", "offer"])
    for c in adults[1:26]:
        w.writerow([c["full_name"], c["mobile"], c["email"], "Diwali personal loan"])
    s3.put_object(Bucket=bucket, Key=EXPORT_KEY, Body=buf.getvalue().encode())
    done.append(f"Bucket {bucket} (no tags) with {EXPORT_KEY}: 25 customers")

    # 3. PAN and mobile in a debug log, in clear text. DPDP Rules, rule 6(1)(a), expects
    #    personal data to be protected, for example by masking; a debug log does neither.
    #    Retention of 7 days, so that anything left behind deletes itself.
    logs = session.client("logs")
    try:
        logs.create_log_group(logGroupName=LOG_GROUP)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    logs.put_retention_policy(logGroupName=LOG_GROUP, retentionInDays=7)
    try:
        logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    now = int(time.time() * 1000)
    events = [{"timestamp": now + i, "message": json.dumps({
        "level": "DEBUG", "path": "/v1/loan-applications", "request": {
            "customer_id": c["customer_id"], "pan": c["pan"], "mobile": c["mobile"], "amount": 50000}})}
        for i, c in enumerate(adults[26:31])]
    logs.put_log_events(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM, logEvents=events)
    done.append(f"Log group {LOG_GROUP}: 5 debug lines with PAN and mobile number")
    return done


def remove(session) -> list[str]:
    account = session.client("sts").get_caller_identity()["Account"]
    names = register.store_names(register.load(), account)
    data = generate_synthetic_data.build(200, 2026)
    c = _adults(data)[0]
    done = []
    session.resource("dynamodb").Table(names["tickets-db"]).delete_item(
        Key={"customer_id": c["customer_id"], "ticket_id": f"S-{c['customer_id']}{TICKET_ID_SUFFIX}"})
    done.append("Ticket removed")

    s3 = session.client("s3")
    bucket = export_bucket(account)
    try:
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                s3.delete_object(Bucket=bucket, Key=obj["Key"])
        s3.delete_bucket(Bucket=bucket)
        done.append(f"Bucket {bucket} removed")
    except s3.exceptions.NoSuchBucket:
        done.append(f"Bucket {bucket} was not there")

    logs = session.client("logs")
    try:
        logs.delete_log_group(logGroupName=LOG_GROUP)
        done.append(f"Log group {LOG_GROUP} removed")
    except logs.exceptions.ResourceNotFoundException:
        done.append(f"Log group {LOG_GROUP} was not there")
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True, help="PlatformEngineer profile, such as dpdp-workload-eng")
    ap.add_argument("--remove", action="store_true", help="remove the three problems")
    args = ap.parse_args(argv)
    import boto3
    session = boto3.Session(profile_name=args.profile, region_name=REGION)
    for line in (remove(session) if args.remove else plant(session)):
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
