"""T19: the company can prove a consent, a change to the ledger is found, and the proof cannot
be deleted.

Control:          DPDP-Act-S6(10)
What is checked:  A consent is recorded through the API. Then, with read-only access, the proof
                  tool (tools/consent_proof.py) must report it VERIFIED: the locked copy, its
                  fingerprint, every ledger field and the notice it cites all match. Then the
                  ledger row is changed, as someone with write access could (the purpose is
                  replaced by another): the proof tool must report the record ALTERED, naming
                  the purpose. The row is put back. Finally, deleting the locked copy must be
                  refused.
Pass means:       The company can produce the notice and the consent for a customer, and a
                  later change to its own records is found, not hidden.
Fail means:       The company could not prove a consent, or could change one without trace.
Evidence stored:  The evidence bucket for the target account.
Who runs it:      The author or reader: pytest --live. The proof is read with the Auditor
                  profile (read-only) in the workload account, PlatformEngineer in the sandbox.
When:             Release 4, Step 8; the clean-room run.
Changes AWS:      Yes: one consent record for C-TEST-0001 (synthetic), locked for 365 days; the
                  ledger row is changed and put back within the test; one evidence record.
"""
import pytest

from tests.conftest import refused
from tests.consent.live import CUSTOMER
from tools import consent_client, consent_proof

pytestmark = pytest.mark.live


def _mine(proof: dict, ref: str) -> dict:
    """The proof result for the record this test made (one purpose, so one record)."""
    return next((r for r in proof["records"] if r.get("request_ref") == ref), {})


def test_t19_consent_can_be_proved(record, target_session, scan_session, published):
    status, answer = consent_client.give(target_session, CUSTOMER, ["fraud-detection"])
    assert status == 201, answer
    ref = answer["request_ref"]

    before = _mine(consent_proof.verify(scan_session, CUSTOMER), ref)

    # Change the ledger row as someone with write access could, then put it back.
    row = next(r for r in consent_proof.ledger_rows(target_session, CUSTOMER)
               if r.get("request_ref") == ref)
    table = target_session.resource("dynamodb").Table(consent_proof.LEDGER)
    key = {"customer_id": CUSTOMER, "record_key": row["record_key"]}

    def set_purpose(value):
        table.update_item(Key=key, UpdateExpression="SET purpose_id = :p",
                          ExpressionAttributeValues={":p": value})

    set_purpose("marketing-offers")
    try:
        altered = _mine(consent_proof.verify(scan_session, CUSTOMER), ref)
    finally:
        set_purpose(row["purpose_id"])
    after = _mine(consent_proof.verify(scan_session, CUSTOMER), ref)

    # Deleting the exact locked copy must be refused.
    bucket = consent_proof.names(target_session)[0]
    s3 = target_session.client("s3")
    delete_refused, delete_resp = refused(lambda: s3.delete_object(
        Bucket=bucket, Key=row["receipt_key"], VersionId=row["receipt_version_id"]))

    detected = (altered.get("status") == "ALTERED"
                and any(p.startswith("purpose_id") for p in altered.get("problems", [])))
    ok = (before.get("status") == "VERIFIED" and detected and after.get("status") == "VERIFIED"
          and delete_refused)
    response = (f"before: {before.get('status')}, lock {before.get('lock')}; after the ledger "
                f"was changed: {altered.get('status')} {altered.get('problems', [])[:1]}; "
                f"after it was put back: {after.get('status')}; delete the locked copy: "
                f"{delete_resp}; request {ref}")
    record("DPDP-Act-S6(10)", "t19-consent-can-be-proved",
           "Produce the proof of a consent with read-only access, change its ledger row, and delete its "
           "locked copy", response, "PASS" if ok else "FAIL", session=target_session)
    assert ok, response
