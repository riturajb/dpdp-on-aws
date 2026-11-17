"""T13: a non-compliant change is stopped at the plan, before it reaches AWS.

Control:          DPDP-Act-S8(1), DPDP-Rule-6(1)(b), DPDP-Rule-6(1)(d), DPDP-Rule-6(1)(e)
What is checked:  scripts/plan_check.sh plans tests/fixtures/noncompliant-stack in the target
                  account: an untagged, unprotected bucket, an unregistered personal table without
                  point-in-time recovery, and a log group kept for 7 days. The check must stop
                  with exit code 3 and name each provision, and nothing may be created.
Pass means:       A change that breaks the rules cannot be applied through the process.
Fail means:       A non-compliant change could reach AWS.
Evidence stored:  The evidence bucket for the target account.
Who runs it:      The author or reader: pytest --live (engineer profile; needs terraform and conftest).
When:             Release 3, Step 7; in the clean-room run before each publication.
Changes AWS:      No. The stack is only planned, never applied. Writes one evidence record.
"""
import os
import subprocess
from pathlib import Path

import pytest

from tests.conftest import env

pytestmark = pytest.mark.live

ROOT = Path(__file__).resolve().parents[2]
STACK = "tests/fixtures/noncompliant-stack"
EXPECTED = ["[s.8(1)]", "[R.6(1)(b)]", "[R.6(1)(d)]", "[R.6(1)(e)]"]


def test_t13_noncompliant_change_is_blocked(record, target, target_session):
    profile = env("DPDP_PROFILE_WORKLOAD" if target == "workload" else "DPDP_PROFILE_SANDBOX")
    run = subprocess.run(["bash", "scripts/plan_check.sh", STACK], cwd=ROOT, capture_output=True,
                         text=True, env=dict(os.environ, TF_VAR_aws_profile=profile))
    out = run.stdout + run.stderr
    missing = [tag for tag in EXPECTED if tag not in out]

    # The check never applies; confirm that the bucket from the stack does not exist.
    account = target_session.client("sts").get_caller_identity()["Account"]
    s3 = target_session.client("s3")
    names = {b["Name"] for b in s3.list_buckets()["Buckets"]}
    created = f"dpdp-unreviewed-export-{account}" in names

    ok = run.returncode == 3 and not missing and not created
    response = (f"plan_check.sh exit code {run.returncode} (3 = blocked); provisions not reported: "
                f"{', '.join(missing) or 'none'}; bucket created: {'yes' if created else 'no'}")
    record("DPDP-Rule-6(1)(b)", "t13-noncompliant-change-is-blocked",
           f"Plan {STACK} through scripts/plan_check.sh", response, "PASS" if ok else "FAIL",
           session=target_session)
    assert ok, response + "\n" + out[-3000:]
