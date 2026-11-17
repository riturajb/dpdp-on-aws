"""T14: a change made outside Terraform is detected and recorded by AWS Config.

Control:          DPDP-Rule-6(1)(g) (the safeguards stay in place), DPDP-Act-S8(1), DPDP-Rule-6(1)(e)
What is checked:  tools/drift_drill.py creates, by hand, a bucket with no DataClass tag and a log
                  group kept for 7 days. AWS Config must mark both NON_COMPLIANT within 15
                  minutes. Both are removed afterwards, whether the test passes or not.
Pass means:       Changes that bypass the plan check are still caught, with the time and resource.
Fail means:       Someone could create a non-compliant store or log group without anyone knowing.
Evidence stored:  The evidence bucket for the target account.
Who runs it:      The author or reader: pytest --live (engineer profile). Takes 2 to 15 minutes.
When:             Release 3, Step 7; in the clean-room run before each publication.
Changes AWS:      For the length of the test: one empty bucket and one empty log group, then
                  removed. Writes one evidence record.
"""
import pytest

from tools import drift_drill

pytestmark = pytest.mark.live


def test_t14_drift_is_detected(record, target_session):
    try:
        drift_drill.plant(target_session)
        found = drift_drill.wait_for_flags(target_session, timeout=900)
    finally:
        drift_drill.remove(target_session)
    ok = None not in found.values()
    response = "; ".join(f"{rule}: " + (f"NON_COMPLIANT after {secs} s" if secs is not None else "not flagged")
                         for rule, secs in found.items())
    record("DPDP-Rule-6(1)(g)", "t14-drift-is-detected",
           "Create an untagged bucket and a 7-day log group by hand; wait for AWS Config",
           response, "PASS" if ok else "FAIL", session=target_session)
    assert ok, response
