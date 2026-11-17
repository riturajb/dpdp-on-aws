"""Fire drill for the detective controls: make two changes outside Terraform and see them flagged.

  python tools/drift_drill.py --profile dpdp-workload-eng --status    # each rule and its result
  python tools/drift_drill.py --profile dpdp-workload-eng             # plant, then wait for the flags
  python tools/drift_drill.py --profile dpdp-workload-eng --remove    # remove both changes

What:        Creates, by hand rather than through Terraform, the two changes that the plan check
             (scripts/plan_check.sh) would have stopped: a bucket with no DataClass tag, and a log
             group that keeps logs for 7 days. Then waits until AWS Config marks both
             NON_COMPLIANT, and prints how long that took.
Why:         Prevention only covers changes made through the process. Someone can still use the
             console or a script. A detective control is trusted only once it has been seen to
             catch such a change (the same reasoning as the Release 2 fire drill).
Who runs it: An engineer (PlatformEngineer, profile dpdp-workload-eng). Test T14 runs the same
             steps and records the evidence.
When:        Release 3, Step 6; again whenever the detective controls change.
Reads:       AWS Config results.   Writes: nothing on the laptop.
Changes AWS: Yes. One empty bucket (dpdp-drift-drill-<account id>) and one empty log group
             (/fernleaf/drift-drill). --remove deletes both. Running it twice is safe.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone

REGION = "ap-south-1"
LOG_GROUP = "/fernleaf/drift-drill"
# Rule names from terraform/modules/detective-controls.
RULE_TAGS = "dpdp-store-has-dataclass"
RULE_LOGS = "dpdp-logs-kept-one-year"
ALL_RULES = [RULE_TAGS, "dpdp-personal-store-registered", "dpdp-bucket-not-public",
             "dpdp-personal-bucket-versioned", "dpdp-personal-table-recoverable", RULE_LOGS]


def drill_bucket(account: str) -> str:
    return f"dpdp-drift-drill-{account}"


def plant(session) -> list[str]:
    account = session.client("sts").get_caller_identity()["Account"]
    s3, logs = session.client("s3"), session.client("logs")
    bucket = drill_bucket(account)
    # A bucket made by hand, without the DataClass tag the rules require (Section 8(1)).
    try:
        s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": REGION})
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass
    # A log group that keeps logs for 7 days, as the debug log of Release 2 did (Rule 6(1)(e)).
    try:
        logs.create_log_group(logGroupName=LOG_GROUP)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    logs.put_retention_policy(logGroupName=LOG_GROUP, retentionInDays=7)
    return [f"Bucket {bucket}: created by hand, no DataClass tag",
            f"Log group {LOG_GROUP}: created by hand, kept for 7 days"]


def flagged(session, rule: str, resource: str, since: datetime | None = None) -> bool:
    """True when AWS Config reports this resource NON_COMPLIANT under this rule. With since,
    only a result recorded after that time counts: a result left over from an earlier drill
    on the same names must not pass for a new detection."""
    cfg = session.client("config")
    pages = cfg.get_paginator("get_compliance_details_by_config_rule").paginate(
        ConfigRuleName=rule, ComplianceTypes=["NON_COMPLIANT"])
    for page in pages:
        for r in page["EvaluationResults"]:
            rid = r["EvaluationResultIdentifier"]["EvaluationResultQualifier"]["ResourceId"]
            if since and r.get("ResultRecordedTime") and r["ResultRecordedTime"] < since:
                continue
            if rid == resource or rid.endswith(resource):
                return True
    return False


def wait_for_flags(session, timeout: int = 900) -> dict:
    """Ask Config to evaluate now, and wait until both changes are flagged.
    Returns {rule: seconds until flagged, or None if not flagged within the timeout}."""
    account = session.client("sts").get_caller_identity()["Account"]
    cfg = session.client("config")
    wanted = {RULE_TAGS: drill_bucket(account), RULE_LOGS: LOG_GROUP}
    found: dict[str, int | None] = {rule: None for rule in wanted}
    start = time.time()
    # A minute's margin allows for a laptop clock slightly ahead of AWS.
    since = datetime.now(timezone.utc) - timedelta(seconds=60)
    last_trigger = 0.0
    while time.time() - start < timeout and None in found.values():
        # The log rule runs on a schedule; ask for an evaluation now, and again every 3 minutes
        # while Config is still recording the new resources.
        if time.time() - last_trigger > 180:
            try:
                cfg.start_config_rules_evaluation(ConfigRuleNames=list(wanted))
            except cfg.exceptions.LimitExceededException:
                pass
            last_trigger = time.time()
        for rule, resource in wanted.items():
            if found[rule] is None and flagged(session, rule, resource, since):
                found[rule] = int(time.time() - start)
        if None in found.values():
            time.sleep(20)
    return found


def status(session) -> list[str]:
    """Each rule and its current result."""
    cfg = session.client("config")
    res = cfg.describe_compliance_by_config_rule(ConfigRuleNames=ALL_RULES)["ComplianceByConfigRules"]
    by = {r["ConfigRuleName"]: r["Compliance"]["ComplianceType"] for r in res}
    return [f"{rule:<34}{by.get(rule, 'NOT FOUND')}" for rule in ALL_RULES]


def remove(session) -> list[str]:
    account = session.client("sts").get_caller_identity()["Account"]
    s3, logs = session.client("s3"), session.client("logs")
    bucket = drill_bucket(account)
    done = []
    try:
        s3.delete_bucket(Bucket=bucket)
        done.append(f"Bucket {bucket} removed")
    except s3.exceptions.NoSuchBucket:
        done.append(f"Bucket {bucket} was not there")
    try:
        logs.delete_log_group(logGroupName=LOG_GROUP)
        done.append(f"Log group {LOG_GROUP} removed")
    except logs.exceptions.ResourceNotFoundException:
        done.append(f"Log group {LOG_GROUP} was not there")
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True, help="PlatformEngineer profile, such as dpdp-workload-eng")
    ap.add_argument("--remove", action="store_true", help="remove the two changes")
    ap.add_argument("--status", action="store_true", help="show each rule and its result")
    args = ap.parse_args(argv)
    import boto3
    session = boto3.Session(profile_name=args.profile, region_name=REGION)
    if args.status:
        print("\n".join(status(session)))
        return 0
    if args.remove:
        print("\n".join(f"  {line}" for line in remove(session)))
        return 0
    for line in plant(session):
        print(f"  {line}")
    print("Waiting for AWS Config (usually 2 to 10 minutes)...", flush=True)
    found = wait_for_flags(session)
    for rule, secs in found.items():
        print(f"  {rule}: " + (f"NON_COMPLIANT after {secs // 60} min {secs % 60} s" if secs is not None
                                else "not flagged within 15 minutes"))
    return 0 if None not in found.values() else 1


if __name__ == "__main__":
    sys.exit(main())
