"""T18: consent reaches the company only through the signed API, and is recorded with its proof.

Control:          DPDP-Act-S6(1), with Rule 6(1)(b) and Rule 6(1)(c)
What is checked:  Against the consent API in the target account:
                    1. a request without an AWS signature is refused by API Gateway (403);
                    2. a signed request with a box ticked in advance is refused by the service
                       (400), naming Section 6(1);
                    3. a signed, valid consent is recorded (201): its locked copy exists, in
                       compliance mode in the workload account (governance mode in the
                       sandbox), its ledger row exists, and the API Gateway access log has a
                       line with the same request reference.
Pass means:       Only signed requests reach the service, only valid consent is recorded, and
                  each record can be traced to the logged request that made it.
Fail means:       Consent could be recorded by anyone, without the conditions of Section 6(1),
                  or without a trace of who sent it.
Evidence stored:  The evidence bucket for the target account.
Who runs it:      The author or reader: pytest --live (engineer profile).
When:             Release 4, Step 8; the clean-room run.
Changes AWS:      Yes: one consent record for C-TEST-0001 (synthetic), locked for 365 days, and
                  one evidence record. The notice is published first if it is not yet current.
"""
import time

import pytest

from tests.consent.live import CUSTOMER, expected_mode
from tools import consent_client, consent_proof

pytestmark = pytest.mark.live

ACCESS_LOG = "/aws/apigateway/dpdp-consent-api"


def _logged(session, ref: str, since_ms: int) -> bool:
    """Wait up to three minutes for the access log line of one request. API Gateway delivers
    access logs to CloudWatch Logs within a minute or two."""
    logs = session.client("logs")
    for _ in range(18):
        found = logs.filter_log_events(logGroupName=ACCESS_LOG, startTime=since_ms,
                                       filterPattern=f'"{ref}"').get("events", [])
        if found:
            return True
        time.sleep(10)
    return False


def test_t18_consent_through_signed_api(record, target, target_session, published):
    since = int(time.time() * 1000) - 60_000
    s1, a1 = consent_client.call(target_session, "GET", "/notice", query={"language": "en"},
                                 sign=False)
    s2, a2 = consent_client.give(target_session, CUSTOMER, ["marketing-offers"],
                                 action="pre_ticked")
    s3, a3 = consent_client.give(target_session, CUSTOMER, ["marketing-offers"])

    unsigned_refused = s1 == 403
    preticked_refused = s2 == 400 and any(x.startswith("[s.6(1)]") for x in a2.get("refused", []))
    mode, row_found, logged = None, False, False
    if s3 == 201:
        rec = a3["recorded"][0]
        bucket = consent_proof.names(target_session)[0]
        mode = target_session.client("s3").get_object_retention(
            Bucket=bucket, Key=rec["receipt_key"],
            VersionId=rec["receipt_version_id"])["Retention"]["Mode"]
        row_found = any(r.get("request_ref") == a3["request_ref"]
                        for r in consent_proof.ledger_rows(target_session, CUSTOMER))
        logged = _logged(target_session, a3["request_ref"], since)

    ok = (unsigned_refused and preticked_refused and s3 == 201 and mode == expected_mode(target)
          and row_found and logged)
    response = (f"unsigned: {s1} {a1.get('message', '')}; pre-ticked: {s2} "
                f"{(a2.get('refused') or [''])[0][:80]}; valid: {s3}, notice {published}, "
                f"locked copy mode {mode}, ledger row {row_found}, access log line {logged}, "
                f"request {a3.get('request_ref')}")
    record("DPDP-Act-S6(1)", "t18-consent-through-signed-api",
           "Send an unsigned request, a pre-ticked consent and a valid consent to the API",
           response, "PASS" if ok else "FAIL", session=target_session)
    assert ok, response
