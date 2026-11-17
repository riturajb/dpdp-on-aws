"""T15: the detective controls cannot be switched off, even by an administrator.

Control:          DPDP-Rule-6(1)(g)
What is checked:  Signed in as BreakGlassAdmin of dpdp-workload, the most powerful role there, try
                  to stop the AWS Config recorder and to delete one of its rules. Both must be
                  refused by the "buckets" guardrail, and the recorder must still be recording.
Pass means:       Detection keeps running; nobody in the account can quietly turn it off.
Fail means:       An administrator could stop detection before making an unnoticed change.
Evidence stored:  The evidence bucket for the workload account.
Who runs it:      The author or reader: pytest --live (workload BreakGlassAdmin profile).
When:             Release 3, Step 7. Runs only when DPDP_TARGET=workload: the guardrail is
                  attached to the Workloads unit, not to the sandbox, which must stay removable.
Changes AWS:      No, if the guardrail works (every attempt is refused). Writes one evidence record.
"""
import pytest

from tests.conftest import refused

pytestmark = pytest.mark.live

RECORDER = "dpdp-recorder"
RULE = "dpdp-store-has-dataclass"


def test_t15_detection_cannot_be_stopped(record, target, target_session, workload_admin_session):
    if target != "workload":
        pytest.skip("Runs against dpdp-workload only: the guardrail is not attached to the sandbox.")
    cfg = workload_admin_session.client("config")
    stop_ok, stop_resp = refused(lambda: cfg.stop_configuration_recorder(ConfigurationRecorderName=RECORDER))
    del_ok, del_resp = refused(lambda: cfg.delete_config_rule(ConfigRuleName=RULE))
    status = cfg.describe_configuration_recorder_status(ConfigurationRecorderNames=[RECORDER])
    recording = status["ConfigurationRecordersStatus"][0]["recording"]
    ok = stop_ok and del_ok and recording
    response = f"stop recorder: {stop_resp}; delete rule: {del_resp}; still recording: {recording}"
    record("DPDP-Rule-6(1)(g)", "t15-detection-cannot-be-stopped",
           f"As BreakGlassAdmin, stop {RECORDER} and delete {RULE}", response,
           "PASS" if ok else "FAIL", session=target_session)
    assert ok, response
