"""T9 to T11: the scanner finds personal data that the register does not know about.

Control:          DPDP-Act-S8(1) (T9, T10) and DPDP-Rule-6(1)(a) (T11)
What is checked:  After tools/plant_findings.py has planted three problems, a scan of the whole
                  account, made with read-only access, finds each one and gives it the right verdict:
                  T9   an Aadhaar number typed into a support ticket: unexpected category
                  T10  a marketing export in a bucket nobody tagged: unregistered store
                  T11  PAN and mobile numbers in a debug log: unregistered store
Pass means:       Personal data outside the register is found, whether or not anyone tagged it.
Fail means:       Personal data can sit in the account without the company knowing.
Evidence stored:  The evidence bucket for the target account.
Who runs it:      The author or reader, after Step 4: pytest --live tests/find
                  The scan uses the read-only Auditor profile (scan_session in conftest.py);
                  the evidence is written with the engineer profile (target_session).
When:             Release 2, Step 6; in the clean-room run before each publication.
Changes AWS:      Writes one evidence record per test to the evidence bucket. Nothing else.
"""
import pytest

from tools import discover, plant_findings, register

pytestmark = pytest.mark.live


# One scan for all three tests: a full scan reads every store, so it is done once per run.
# If the planted bucket is missing, the tests are skipped rather than failed: the control has
# not been exercised, which is different from the control failing.
@pytest.fixture(scope="module")
def findings(scan_session, target_session):
    account = target_session.client("sts").get_caller_identity()["Account"]
    s3 = target_session.client("s3")
    try:
        s3.head_bucket(Bucket=plant_findings.export_bucket(account))
    except Exception:
        pytest.skip("The planted problems are not there. Run tools/plant_findings.py first (Release 2 guide).")
    col, acct = discover.scan_account(scan_session)
    return discover.reconcile(col, register.load(), acct)


# A test passes only if the planted problem is found AND every matching finding has the right
# verdict. Found with the wrong verdict is a FAIL: the company would misjudge the problem.
def _check(record, target_session, findings, control, test, attempted, match, verdict):
    hits = [f for f in findings if match(f)]
    ok = bool(hits) and all(f.verdict == verdict for f in hits)
    response = "; ".join(f"{f.store_name} {f.field} {f.identifier} {f.confidence} x{f.count}: {f.verdict}"
                         for f in hits) or "Not found"
    record(control, test, attempted, response, "PASS" if ok else "FAIL", session=target_session)
    assert ok, response


def test_t9_aadhaar_in_ticket_notes(record, target_session, findings):
    _check(record, target_session, findings, "DPDP-Act-S8(1)", "t9-aadhaar-in-ticket-notes",
           "Scan the account for Aadhaar numbers outside the stores and fields the register lists",
           lambda f: f.identifier == "aadhaar" and f.store_name == "dpdp-support-tickets",
           "unexpected category")


def test_t10_untagged_marketing_export(record, target_session, findings):
    account = target_session.client("sts").get_caller_identity()["Account"]
    bucket = plant_findings.export_bucket(account)
    _check(record, target_session, findings, "DPDP-Act-S8(1)", "t10-untagged-marketing-export",
           "Scan every bucket in the account, tagged or not, for personal data",
           lambda f: f.store_name == bucket and f.identifier == "mobile",
           "unregistered store")


def test_t11_personal_data_in_debug_log(record, target_session, findings):
    _check(record, target_session, findings, "DPDP-Rule-6(1)(a)", "t11-personal-data-in-debug-log",
           "Scan every log group in the account for personal data",
           lambda f: f.store_name == plant_findings.LOG_GROUP and f.identifier in ("pan", "mobile"),
           "unregistered store")
