"""Call the consent service the way Fernleaf's app would: show the notice, send consents.

  python tools/consent_client.py notice --profile dpdp-workload-eng [--language hi]
  python tools/consent_client.py give --customer C-TEST-0001 --purpose marketing-offers \
      --profile dpdp-workload-eng
  python tools/consent_client.py give ... --pre-ticked        # a box ticked in advance
  python tools/consent_client.py give ... --unsigned          # no AWS signature
  python tools/consent_client.py deliver --customer C-TEST-0001 --channel sms \
      --profile dpdp-workload-eng

What:        Sends one request to the consent API (terraform/modules/consent-service) and prints
             the answer. Every request is signed with the credentials of the profile given
             (AWS Signature Version 4), as the API requires. The options --pre-ticked,
             --bundled, --extra-field, --old-notice and --unsigned send the kinds of request the
             law does not accept, so that their refusal can be seen.
Why:         DPDP Act, Section 5(1): the notice is shown with or before the request. Section
             6(1): consent is specific, informed, by a clear affirmative action, and limited to
             the data needed. Rule 6(1)(b): only signed requests reach the service. Seeing a bad
             request refused, with the provision named, is how the control is trusted.
Who runs it: An engineer (PlatformEngineer), standing in for the app. The tests (T18 to T20),
             tools/old_consents.py and the demonstration use its functions.
When:        Release 4, Step 5.
Reads:       The API's address, found by its name in the account.   Writes: nothing locally.
Changes AWS: give and deliver: each accepted request adds one locked record and one ledger row
             per purpose. They cannot be removed for 365 days in the workload account, by design.
             Refused requests change nothing.

The app, not this service, signs the customer in. In a real deployment the app's back end calls
the API with its own role, after it has authenticated the customer; the customer number it sends
is the one of the signed-in customer. This build does not include an app.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGION = "ap-south-1"
API_NAME = "dpdp-consent-api"      # set in terraform/modules/consent-service


_ENDPOINTS: dict[int, str] = {}


def endpoint(session) -> str:
    """The API's address (https://<id>.execute-api.ap-south-1.amazonaws.com), found by name, so
    nothing has to be copied into config/local.env. Looked up once per session, then reused."""
    if id(session) not in _ENDPOINTS:
        apis = session.client("apigatewayv2").get_apis(MaxResults="100")["Items"]
        found = [a["ApiEndpoint"] for a in apis if a["Name"] == API_NAME]
        if not found:
            raise SystemExit(f"No API named {API_NAME} in this account. "
                             "Run Release 4, Step 3 first.")
        _ENDPOINTS[id(session)] = found[0]
    return _ENDPOINTS[id(session)]


def call(session, method: str, path: str, body: dict | None = None,
         query: dict | None = None, sign: bool = True) -> tuple[int, dict]:
    """Send one request and return (HTTP status, answer as a dictionary).

    Signing: botocore, which boto3 already installs, adds the AWS Signature Version 4 headers
    for the service "execute-api". API Gateway checks them against IAM before the request
    reaches the function; an unsigned or wrongly signed request never reaches it."""
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    url = endpoint(session) + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"content-type": "application/json"} if data else {}
    req = AWSRequest(method=method, url=url, data=data, headers=headers)
    if sign:
        creds = session.get_credentials().get_frozen_credentials()
        SigV4Auth(creds, "execute-api", REGION).add_auth(req)
    prepared = req.prepare()
    http = urllib.request.Request(prepared.url, data=prepared.body, method=method,
                                  headers=dict(prepared.headers))
    try:
        with urllib.request.urlopen(http, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read() or b"{}"
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"message": raw.decode("utf-8", "replace")}


def get_notice(session, language: str = "en") -> dict:
    """The current notice, as the app shows it before asking for consent."""
    status, answer = call(session, "GET", "/notice", query={"language": language})
    if status != 200:
        raise SystemExit(f"The notice could not be read ({status}): {answer}")
    return answer


def consent_request(customer: str, purposes: list[str], notice_version: str,
                    language: str = "en", channel: str = "app", action: str = "customer_ticked",
                    bundled: bool = False, extra_field: str | None = None) -> dict:
    """The body the app sends when the person presses Agree: one choice per purpose ticked.
    bundled and extra_field build the two kinds of request Section 6(1) does not allow."""
    if bundled:
        choices = [{"purpose_id": purposes, "action": action}]
    else:
        choices = [{"purpose_id": p, "action": action} for p in purposes]
    if extra_field:
        for ch in choices:
            ch["fields"] = [extra_field]
    return {"customer_id": customer, "notice_version": notice_version, "language": language,
            "channel": channel, "choices": choices}


def give(session, customer: str, purposes: list[str], **kw) -> tuple[int, dict]:
    """Show the notice first (Section 5(1)), then send the consent for that notice version."""
    old = kw.pop("old_notice", False)
    sign = kw.pop("sign", True)
    notice = get_notice(session, kw.get("language", "en"))
    version = "N-000000000000" if old else notice["notice_version"]
    body = consent_request(customer, purposes, version, **kw)
    return call(session, "POST", "/consents", body=body, sign=sign)


def deliver(session, customer: str, channel: str = "sms", language: str = "en",
            version: str | None = None) -> tuple[int, dict]:
    """Record that the current notice was delivered to an earlier customer (Section 5(2)).
    version: the current notice version, when the caller already has it (saves a request)."""
    version = version or get_notice(session, language)["notice_version"]
    body = {"customer_id": customer, "notice_version": version,
            "language": language, "channel": channel}
    return call(session, "POST", "/notice-deliveries", body=body)


def show(status: int, answer: dict) -> None:
    """Print the answer: each refusal on its own line, or what was recorded."""
    print(f"HTTP {status}")
    if "refused" in answer:
        for line in answer["refused"]:
            print(f"  REFUSED {line}")
        print("  Nothing was recorded.")
    elif "recorded" in answer:
        for r in answer["recorded"]:
            print(f"  RECORDED {r['purpose_id']}  sha256 {r['sha256'][:16]}...")
            print(f"           {r['receipt_key']}")
        print(f"  notice {answer['notice_version']} at {answer['recorded_at']}")
    else:
        print("  " + json.dumps(answer, ensure_ascii=False))
    if answer.get("request_ref"):
        print(f"  request reference {answer['request_ref']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("notice", help="show the current notice")
    n.add_argument("--language", default="en")
    g = sub.add_parser("give", help="send a consent")
    g.add_argument("--customer", required=True)
    g.add_argument("--purpose", action="append", required=True,
                   help="a purpose id from the notice; repeat for several")
    g.add_argument("--language", default="en")
    g.add_argument("--channel", default="app")
    g.add_argument("--pre-ticked", action="store_true", help="the box was ticked in advance")
    g.add_argument("--bundled", action="store_true", help="all purposes as one choice")
    g.add_argument("--extra-field", help="ask for a data item the purpose does not need")
    g.add_argument("--old-notice", action="store_true", help="cite a notice that is not current")
    g.add_argument("--unsigned", action="store_true", help="send without an AWS signature")
    d = sub.add_parser("deliver", help="record that the notice reached an earlier customer")
    d.add_argument("--customer", required=True)
    d.add_argument("--channel", default="sms")
    for p in (n, g, d):
        p.add_argument("--profile", required=True)
    args = ap.parse_args(argv)

    import boto3
    session = boto3.Session(profile_name=args.profile, region_name=REGION)
    if args.cmd == "notice":
        answer = get_notice(session, args.language)
        print(f"Notice {answer['notice_version']} ({answer['language']}), "
              f"sha256 {answer['notice_sha256'][:16]}...")
        print(f"Choices: {', '.join(answer['choices'])}\n")
        print(answer["text"])
        return 0
    if args.cmd == "deliver":
        status, answer = deliver(session, args.customer, args.channel)
        show(status, answer)
        return 0 if status == 201 else 1
    status, answer = give(session, args.customer, args.purpose, language=args.language,
                          channel=args.channel,
                          action="pre_ticked" if args.pre_ticked else "customer_ticked",
                          bundled=args.bundled, extra_field=args.extra_field,
                          old_notice=args.old_notice, sign=not args.unsigned)
    show(status, answer)
    return 0 if status == 201 else 1


if __name__ == "__main__":
    sys.exit(main())
