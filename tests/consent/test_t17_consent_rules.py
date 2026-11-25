"""T17: the consent service accepts only consent that meets Section 6(1), and records it whole.

Control:          DPDP-Act-S6(1)
What is checked:  The consent service's own code (services/consent/handler.py) is given eleven
                  requests, with a stand-in for AWS so that nothing leaves the laptop:
                    accepted   two purposes, each ticked by the person, against the current
                               notice: two locked copies and two ledger rows, whose
                               fingerprints match
                    refused    a box ticked in advance; several purposes as one choice; a
                               purpose processed under Section 7; the record of consent chosen
                               on its own; a purpose not in the notice;
                               a data item the purpose does not need; a notice that is not the
                               current one; a language that is not offered; a mobile number in
                               place of a customer number; and one good choice with one bad one
                  Every refusal must name its provision, and a refused request must leave no
                  record at all.
Pass means:       Only valid consent is recorded; invalid consent is refused, with the reason,
                  and never partly recorded.
Fail means:       The company could hold a "consent" that the law does not recognise.
Evidence stored:  Locally (offline test, also run in GitHub Actions).
Who runs it:      Anyone, with no AWS access; also GitHub Actions on every pull request.
When:             Release 4, Steps 1 and 8; after every change to services/consent.
Changes AWS:      No.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "consent"))

import consent_rules as rules  # noqa: E402
import handler  # noqa: E402

from tools import notice, register  # noqa: E402

CUSTOMER = "C-TEST-0001"


class FakeStore:
    """Stands in for AWS: the notices bucket, the records bucket and the ledger, in memory.
    put_ledger refuses to replace a row, as the real condition expression does."""

    def __init__(self, built: dict):
        self.version = notice.version(built)
        self.built = built
        self.receipts: dict[str, bytes] = {}
        self.ledger: dict[str, dict] = {}

    def current(self):
        return {"version": self.version, "sha256": rules.fingerprint(self.built)}

    def notice(self, version):
        if version != self.version:
            raise KeyError(version)   # as S3 would answer NoSuchKey
        return self.built

    def text(self, version, language):
        return self.built["texts"][language]

    def put_receipt(self, key, body):
        self.receipts[key] = body
        return f"v{len(self.receipts)}"

    def put_ledger(self, item):
        if item["record_key"] in self.ledger:
            raise ValueError("ConditionalCheckFailed")
        self.ledger[item["record_key"]] = item


def event(route: str, body: dict, ref: str) -> dict:
    """A request as API Gateway passes it to the function (payload format 2.0)."""
    arn = "arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_PlatformEngineer_x/someone"
    return {"routeKey": route, "body": json.dumps(body),
            "requestContext": {"requestId": ref,
                               "authorizer": {"iam": {"userArn": arn}}}}


def consent(version: str, *choices, **over) -> dict:
    body = {"customer_id": CUSTOMER, "notice_version": version, "language": "en",
            "channel": "app", "choices": list(choices)}
    body.update(over)
    return body


def tick(purpose, **extra):
    return {"purpose_id": purpose, "action": rules.AFFIRMATIVE_ACTION, **extra}


def test_t17_consent_rules(record):
    built = notice.build(register.load())
    store = FakeStore(built)
    v = store.version
    outcomes, ok = [], True

    # Accepted: two purposes, each ticked by the person.
    resp = handler.handle(event("POST /consents",
                                consent(v, tick("marketing-offers"), tick("fraud-detection")),
                                "req-accepted"), store)
    rows = list(store.ledger.values())
    good = (resp["statusCode"] == 201 and len(rows) == 2 and len(store.receipts) == 2
            and all(rules.fingerprint(json.loads(store.receipts[r["receipt_key"]]))
                    == r["receipt_sha256"] for r in rows)
            and all(json.loads(store.receipts[r["receipt_key"]])["caller"]
                    == "AWSReservedSSO_PlatformEngineer_x" for r in rows))
    outcomes.append(f"valid: {resp['statusCode']}, {len(rows)} records")
    ok &= good

    refused_cases = [
        ("box ticked in advance", consent(v, {"purpose_id": "marketing-offers",
                                              "action": "pre_ticked"}), "[s.6(1)]"),
        ("purposes bundled", consent(v, {"purpose_id": ["marketing-offers", "credit-check"],
                                         "action": rules.AFFIRMATIVE_ACTION}), "[s.6(1)]"),
        ("Section 7 purpose", consent(v, tick("complaint-handling")), "[s.6(1)]"),
        ("record of consent on its own", consent(v, tick("consent-proof")), "[s.6(1)]"),
        ("purpose not in notice", consent(v, tick("sell-data-to-partners")), "[s.6(1)]"),
        ("data not needed", consent(v, tick("marketing-offers", fields=["aadhaar_number"])),
         "[s.6(1)]"),
        ("old notice", consent("N-000000000000", tick("marketing-offers")), "[s.5(1)]"),
        ("language not offered", consent(v, tick("marketing-offers"), language="ta"),
         "[s.6(3)]"),
        ("mobile number as customer", consent(v, tick("marketing-offers"),
                                              customer_id="9876543210"), "[input]"),
        ("one good, one bad", consent(v, tick("credit-check"),
                                      {"purpose_id": "wallet-payments", "action": "default"}),
         "[s.6(1)]"),
    ]
    before = (len(store.receipts), len(store.ledger))
    for i, (name, body, tag) in enumerate(refused_cases):
        resp = handler.handle(event("POST /consents", body, f"req-refused-{i}"), store)
        answer = json.loads(resp["body"])
        named = any(line.startswith(tag) for line in answer.get("refused", []))
        this_ok = resp["statusCode"] == 400 and named
        outcomes.append(f"{name}: {resp['statusCode']} {tag if named else 'no ' + tag}")
        ok &= this_ok
    nothing_written = (len(store.receipts), len(store.ledger)) == before
    outcomes.append(f"records added by refused requests: "
                    f"{len(store.receipts) - before[0]}")
    ok &= nothing_written

    response = "; ".join(outcomes)
    record("DPDP-Act-S6(1)", "t17-consent-rules",
           "Send one valid and ten invalid consent requests to the service's code",
           response, "PASS" if ok else "FAIL", account="offline")
    assert ok, response
