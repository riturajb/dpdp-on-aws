"""The consent service: shows the notice, and records each consent with its proof.

What:        An AWS Lambda function behind an API Gateway HTTP API. Three routes, each open
             only to callers who sign their request with AWS credentials (IAM authorisation):
               GET  /notice?language=en       the current notice, as the person sees it
               POST /consents                 record the purposes a person agreed to
               POST /notice-deliveries        record that an earlier customer was given the
                                              notice (Section 5(2))
             A consent is checked against the notice the person was shown (consent_rules.py).
             If it passes, each purpose gets two records: a locked copy in an S3 bucket with
             Object Lock (the proof), and a row in a DynamoDB ledger (the index), which holds
             the locked copy's location and SHA-256 fingerprint.
Why:         DPDP Act, Sections 5(1), 6(1), 6(3) and 6(10): a notice with or before every
             request, consent that meets the conditions of Section 6(1), and proof of both that
             the company can produce in a proceeding. A locked copy cannot be changed or
             deleted before its retention date, even by an administrator (compliance mode in
             the workload account), so the proof holds even if the ledger is altered.
Who runs it: AWS, for each request to the API. In this project the app is played by the
             tools (tools/consent_client.py) and the tests, signed in as PlatformEngineer.
When:        Release 4 onwards. Deployed by terraform/modules/consent-service.
Reads:       The notice from the notices bucket (written by tools/notice.py publish).
Writes:      One locked object and one ledger row per purpose consented to, or per notice
             delivered. Nothing else. Its role cannot update or delete either.
Changes AWS: Yes, as above, for each accepted request.

What it logs: the API's request reference, the route, the outcome and the number of records.
It never logs the customer number or the body of a request, so its log holds no personal data
(Rule 6(1)(a)); the request reference links the log line to the record when needed.

Settings come from environment variables set by Terraform: NOTICES_BUCKET, RECORDS_BUCKET and
LEDGER_TABLE.
"""
from __future__ import annotations

import base64
import json
import os

import consent_rules as rules

# ---------------------------------------------------------------- storage

class AwsStore:
    """Reads the notice and writes the two records, in the AWS account the function runs in.

    The offline test (T17) uses a stand-in with the same four methods, so the handler's logic
    is tested without AWS."""

    def __init__(self):
        import boto3  # included in the Lambda runtime; imported here so tests need no AWS
        self.s3 = boto3.client("s3")
        self.ledger = boto3.client("dynamodb")
        self.notices = os.environ["NOTICES_BUCKET"]
        self.records = os.environ["RECORDS_BUCKET"]
        self.table = os.environ["LEDGER_TABLE"]

    def current(self) -> dict:
        """notices/current.json: which notice version is shown today, and its fingerprint."""
        body = self.s3.get_object(Bucket=self.notices, Key="notices/current.json")["Body"]
        return json.loads(body.read())

    def notice(self, version: str) -> dict:
        """The notice content of one version: the catalogue of purposes and data items."""
        body = self.s3.get_object(Bucket=self.notices,
                                  Key=f"notices/{version}/notice.json")["Body"]
        return json.loads(body.read())

    def text(self, version: str, language: str) -> str:
        """The notice as the person reads it, in one language."""
        body = self.s3.get_object(Bucket=self.notices,
                                  Key=f"notices/{version}/notice.{language}.txt")["Body"]
        return body.read().decode("utf-8")

    def put_receipt(self, key: str, body: bytes) -> str:
        """Write the locked copy. The bucket's default retention locks it on arrival; a
        checksum is required by S3 for every write to an Object Lock bucket. Returns the
        version id, which names this exact copy for ever."""
        resp = self.s3.put_object(Bucket=self.records, Key=key, Body=body,
                                  ContentType="application/json", ChecksumAlgorithm="SHA256")
        return resp["VersionId"]

    def put_ledger(self, item: dict) -> None:
        """Add the ledger row. The condition refuses to replace a row that already exists, so a
        record can only be added, never overwritten through this service."""
        self.ledger.put_item(
            TableName=self.table,
            Item={k: {"S": str(v)} for k, v in item.items()},
            ConditionExpression="attribute_not_exists(record_key)",
        )


# ---------------------------------------------------------------- helpers

def _reply(status: int, payload: dict) -> dict:
    """An HTTP response in the format API Gateway expects from Lambda (payload version 2.0)."""
    return {"statusCode": status, "headers": {"content-type": "application/json"},
            "body": json.dumps(payload, ensure_ascii=False)}


def _body(event: dict) -> dict | None:
    """The request body as a dictionary, or None if it is not a JSON object."""
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _caller(event: dict) -> str:
    """Which role signed the request, without the session name or the account id.

    An assumed-role ARN ends in .../<role name>/<session name>; the session name is usually the
    person's sign-in name, which is personal data and is not needed in the record."""
    arn = (event.get("requestContext", {}).get("authorizer", {}).get("iam", {})
           .get("userArn", ""))
    parts = arn.split("/")
    return parts[1] if len(parts) >= 3 and ":assumed-role" in parts[0] else "unknown"


def _log(ref: str, route: str, outcome: str, records: int = 0) -> None:
    """One log line per request, with no personal data (see the module description)."""
    print(json.dumps({"request_ref": ref, "route": route, "outcome": outcome,
                      "records": records}))


# ---------------------------------------------------------------- routes

def _get_notice(event, store, ref):
    """GET /notice: the current notice text, its version and its fingerprint."""
    language = (event.get("queryStringParameters") or {}).get("language", "en")
    cur = store.current()
    notice = store.notice(cur["version"])
    if language not in notice["languages"]:
        _log(ref, "GET /notice", "refused")
        return _reply(400, {"refused": [f"[s.5(3)] Language '{language}' is not offered."],
                            "request_ref": ref})
    _log(ref, "GET /notice", "shown")
    return _reply(200, {"notice_version": cur["version"], "notice_sha256": cur["sha256"],
                        "language": language, "text": store.text(cur["version"], language),
                        "choices": [c["purpose_id"] for c in notice["choices"]],
                        "request_ref": ref})


def _record(store, records: list[dict]) -> list[dict]:
    """Write each record: first the locked copy, then the ledger row that points to it.

    The order matters. If a write fails (rare: AWS unavailable for a moment), the service
    answers 500 and the caller sends the request again. A locked copy written before the failure
    stays, and the proof tool lists it as a locked copy the ledger does not mention; the reverse,
    a ledger row with no proof behind it, cannot happen."""
    out = []
    for rec in records:
        body = rules.canonical(rec)
        sha = rules.fingerprint(rec)
        key = rules.receipt_key(rec)
        version_id = store.put_receipt(key, body)
        store.put_ledger(rules.ledger_item(rec, key, version_id, sha))
        out.append({"purpose_id": rec["purpose_id"], "receipt_key": key,
                    "receipt_version_id": version_id, "sha256": sha})
    return out


def _post_consents(event, store, ref):
    """POST /consents: check the request as a whole. If any part is refused, nothing is
    recorded; if all of it passes, one record is made for each purpose."""
    body = _body(event)
    if body is None:
        _log(ref, "POST /consents", "refused")
        return _reply(400, {"refused": ["[input] The body must be a JSON object."],
                            "request_ref": ref})
    # Only the current notice is loaded. A request citing any other version is refused by the
    # check (Section 5(1)), so a version name sent by the caller is never used to read a file.
    cur = store.current()
    notice = store.notice(cur["version"])
    refusals, choices = rules.check_consent(body, notice, cur["version"])
    if refusals:
        _log(ref, "POST /consents", "refused")
        return _reply(400, {"refused": refusals, "request_ref": ref})
    at = rules.now_ist()
    caller = _caller(event)
    records = [rules.consent_record(body, ch, cur["sha256"], ref, caller, at) for ch in choices]
    done = _record(store, records)
    _log(ref, "POST /consents", "recorded", len(done))
    return _reply(201, {"recorded": done, "notice_version": cur["version"],
                        "recorded_at": at, "request_ref": ref})


def _post_delivery(event, store, ref):
    """POST /notice-deliveries: record that an earlier customer was given the current notice."""
    body = _body(event)
    if body is None:
        _log(ref, "POST /notice-deliveries", "refused")
        return _reply(400, {"refused": ["[input] The body must be a JSON object."],
                            "request_ref": ref})
    cur = store.current()
    notice = store.notice(cur["version"])
    refusals = rules.check_delivery(body, notice, cur["version"])
    if refusals:
        _log(ref, "POST /notice-deliveries", "refused")
        return _reply(400, {"refused": refusals, "request_ref": ref})
    at = rules.now_ist()
    rec = rules.delivery_record(body, cur["sha256"], ref, _caller(event), at)
    done = _record(store, [rec])
    _log(ref, "POST /notice-deliveries", "recorded", 1)
    return _reply(201, {"recorded": done, "notice_version": cur["version"],
                        "recorded_at": at, "request_ref": ref})


ROUTES = {"GET /notice": _get_notice, "POST /consents": _post_consents,
          "POST /notice-deliveries": _post_delivery}


def handle(event: dict, store) -> dict:
    """Route one request. Kept apart from lambda_handler so that the tests can pass their own
    store. Unexpected errors return 500 with the request reference, and log only the error
    type: an error message could contain part of the request."""
    ctx = event.get("requestContext", {})
    ref = ctx.get("requestId", "no-request-id")
    route = event.get("routeKey", "")
    fn = ROUTES.get(route)
    if fn is None:
        return _reply(404, {"error": f"No route {route}", "request_ref": ref})
    try:
        return fn(event, store, ref)
    except Exception as e:  # noqa: BLE001 - report every failure the same way, without detail
        _log(ref, route, f"error {type(e).__name__}")
        return _reply(500, {"error": "The record was not made. Try again.", "request_ref": ref})


_STORE = None


def lambda_handler(event, context):  # noqa: ARG001 - the signature AWS Lambda calls
    """Entry point for AWS Lambda. The store is created once per container and reused."""
    global _STORE
    if _STORE is None:
        _STORE = AwsStore()
    return handle(event, _STORE)
