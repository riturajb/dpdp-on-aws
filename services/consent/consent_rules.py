"""The rules a consent must meet before it is recorded, and the shape of each record.

What:        Pure functions, with no AWS calls: check a request against the notice the person
             was shown, and build the records that prove it. The consent service
             (handler.py) calls them for every request; the offline test T17 calls them
             directly, and tools/notice.py and tools/consent_proof.py use the same
             fingerprint function, so a record made by one can be checked by the others.
Why:         DPDP Act, Section 6(1): consent must be free, specific, informed, unconditional
             and unambiguous, given by a clear affirmative action, and limited to the data
             needed for the purpose. Section 5(1): a notice must come with or before the
             request. Section 6(3): the request is offered in English or a language of the
             Eighth Schedule. Section 6(10): the company must be able to prove all of this.
             A rule that is written as code is applied the same way to every request.
Who runs it: Nobody directly. It is part of the consent service (AWS Lambda) and is loaded by
             the tools and tests.
When:        Release 4 onwards.
Reads:       Nothing outside its arguments.   Writes: nothing.
Changes AWS: No.

Every refusal starts with the provision it serves, as the plan check does in Release 3, so a
refused request explains itself:  [s.6(1)] ... , [s.5(1)] ... , [s.6(3)] ...
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

# India Standard Time has no daylight saving, so a fixed offset is exact. A fixed offset also
# avoids depending on the time zone database, which the Lambda runtime may not include.
IST = timezone(timedelta(hours=5, minutes=30))

# The only action that counts as "a clear affirmative action" (Section 6(1)): the person ticked
# the box herself. Anything else (a box ticked in advance, a default, silence) is refused.
AFFIRMATIVE_ACTION = "customer_ticked"

# Where a consent may be given, and how an old notice may be delivered (Section 5(2)).
CONSENT_CHANNELS = {"app", "web", "branch"}
DELIVERY_CHANNELS = {"sms", "email", "app"}

# Customer numbers are the company's internal references (C-104882, C-TEST-0001). Checking
# the format keeps anything else, such as a mobile number or free text, out of the records.
CUSTOMER_ID = re.compile(r"^C-[A-Z0-9-]{4,20}$")


# ---------------------------------------------------------------- fingerprints

def canonical(value) -> bytes:
    """The one agreed byte form of a JSON value: keys sorted, no spaces, UTF-8.

    Two copies of the same record always give the same bytes, so their SHA-256 fingerprints
    match; a single changed character gives a different fingerprint.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def fingerprint(value) -> str:
    """SHA-256 of the canonical form, as 64 hexadecimal characters."""
    return hashlib.sha256(canonical(value)).hexdigest()


def notice_version(notice: dict) -> str:
    """The notice's version name, derived from its content: N- and the first 12 characters of
    its fingerprint. Any change to the notice gives a new version name; the same content always
    gives the same name, so a version can never silently mean two different texts."""
    return "N-" + fingerprint(notice)[:12]


def now_ist() -> str:
    """The current time in IST, to the second, for the record. The service sets the time
    itself; a time sent by the caller is never trusted."""
    return datetime.now(IST).isoformat(timespec="seconds")


# ---------------------------------------------------------------- checks

def check_consent(body: dict, notice: dict, current_version: str) -> tuple[list[str], list[dict]]:
    """Check one consent request against the notice it says the person was shown.

    body:            the request, as sent by the app:
                       {"customer_id": "C-TEST-0001", "notice_version": "N-...",
                        "language": "en", "channel": "app",
                        "choices": [{"purpose_id": "marketing-offers",
                                     "action": "customer_ticked",
                                     "fields": ["marketing_opt_in"]}]}
                     "choices" lists the purposes the person agreed to, one entry each.
                     "fields" is optional; when given, it must stay within the purpose's data.
    notice:          the notice content for that version (built by tools/notice.py).
    current_version: the version the company shows today.

    Returns (refusals, choices). If refusals is empty, every choice may be recorded; choices
    then carries, for each purpose, what the record needs. If anything is refused, the whole
    request is refused and nothing is recorded, so a partly valid request never leaves a partial
    consent behind (Section 6(2) makes the infringing part invalid; this service refuses it
    before it exists).
    """
    refusals: list[str] = []

    # --- who: an internal customer number, never an identifier such as a mobile number.
    cid = body.get("customer_id")
    if not isinstance(cid, str) or not CUSTOMER_ID.match(cid):
        refusals.append("[input] customer_id must be an internal customer number such as "
                        "C-104882.")

    # --- Section 5(1): the notice must come with or before the request, and it must be the
    # notice the company uses today. An older version may describe processing that has changed.
    version = body.get("notice_version")
    if not version:
        refusals.append("[s.5(1)] No notice version given. The notice must be shown with or "
                        "before the request for consent.")
    elif version != current_version:
        refusals.append(f"[s.5(1)] Notice {version} is not the current notice "
                        f"({current_version}). Show the current notice first.")

    # --- Section 6(3): the request is offered in English or a language of the Eighth
    # Schedule; it must be one the company has the notice in.
    language = body.get("language")
    if language not in notice.get("languages", []):
        refusals.append(f"[s.6(3)] Language '{language}' is not offered. The notice is "
                        f"available in: {', '.join(notice.get('languages', []))}.")

    channel = body.get("channel")
    if channel not in CONSENT_CHANNELS:
        refusals.append(f"[input] channel must be one of: {', '.join(sorted(CONSENT_CHANNELS))}.")

    # --- Section 6(1): specific, one choice per purpose, each a clear affirmative action,
    # limited to the data the purpose needs.
    offered = {c["purpose_id"]: c for c in notice.get("choices", [])}
    not_asked = {p["purpose_id"]: p for p in notice.get("not_consent", [])}
    with_each = {p["purpose_id"] for p in notice.get("with_each_consent", [])}
    choices = body.get("choices")
    accepted: list[dict] = []
    if not isinstance(choices, list) or not choices:
        refusals.append("[s.6(1)] No purpose chosen. Consent is given for a specified purpose, "
                        "one choice per purpose.")
        choices = []
    seen: set[str] = set()
    for i, ch in enumerate(choices, start=1):
        if not isinstance(ch, dict):
            refusals.append(f"[s.6(1)] Choice {i} is not a single purpose.")
            continue
        pid = ch.get("purpose_id")
        # A list of purposes, or a word such as "all", is a bundled consent: refused.
        if not isinstance(pid, str):
            refusals.append(f"[s.6(1)] Choice {i} bundles several purposes. Each purpose is a "
                            "separate choice.")
            continue
        if pid in seen:
            refusals.append(f"[s.6(1)] Purpose '{pid}' is chosen twice.")
            continue
        seen.add(pid)
        if pid in not_asked:
            refusals.append(f"[s.6(1)] Purpose '{pid}' is processed under Section "
                            f"{not_asked[pid]['basis'][1:]}, not on consent. Asking for consent "
                            "to it would mislead the person.")
            continue
        if pid in with_each:
            refusals.append(f"[s.6(1)] Purpose '{pid}' is part of every consent; it is not "
                            "chosen on its own.")
            continue
        if pid not in offered:
            refusals.append(f"[s.6(1)] Purpose '{pid}' is not in the current notice. Consent "
                            "can only be given to a purpose the person was told about.")
            continue
        action = ch.get("action")
        if action != AFFIRMATIVE_ACTION:
            refusals.append(f"[s.6(1)] Purpose '{pid}': the action was '{action}'. Consent needs "
                            "a clear affirmative action by the person; a box ticked in advance or "
                            "a default is not consent.")
            continue
        allowed = set(offered[pid]["fields"])
        asked = ch.get("fields", sorted(allowed))
        if not isinstance(asked, list) or not asked:
            refusals.append(f"[s.6(1)] Purpose '{pid}': fields must be a list of data items.")
            continue
        extra = sorted(set(asked) - allowed)
        if extra:
            refusals.append(f"[s.6(1)] Purpose '{pid}' does not need {', '.join(extra)}. Consent "
                            "is limited to the data needed for the purpose.")
            continue
        accepted.append({"purpose_id": pid, "category_id": offered[pid]["category_id"],
                         "fields": sorted(asked), "action": action})
    return refusals, ([] if refusals else accepted)


def check_delivery(body: dict, notice: dict, current_version: str) -> list[str]:
    """Check a record that a notice was delivered to a person whose consent was given before
    the Act's obligations began (Section 5(2)). Same checks on the customer, the notice
    version and the language as for a consent; the channel is how it was delivered."""
    refusals: list[str] = []
    cid = body.get("customer_id")
    if not isinstance(cid, str) or not CUSTOMER_ID.match(cid):
        refusals.append("[input] customer_id must be an internal customer number such as "
                        "C-104882.")
    if body.get("notice_version") != current_version:
        refusals.append(f"[s.5(2)] Only the current notice ({current_version}) is delivered.")
    if body.get("language") not in notice.get("languages", []):
        refusals.append(f"[s.5(3)] Language '{body.get('language')}' is not offered.")
    if body.get("channel") not in DELIVERY_CHANNELS:
        refusals.append(f"[input] channel must be one of: "
                        f"{', '.join(sorted(DELIVERY_CHANNELS))}.")
    return refusals


# ---------------------------------------------------------------- records

def consent_record(body: dict, choice: dict, notice_sha256: str, request_ref: str,
                   caller: str, recorded_at: str) -> dict:
    """The record of one consent to one purpose: everything needed to prove it later
    (Section 6(10)), and nothing more. It holds the internal customer number and no name,
    identifier or other personal data (Rule 6(1)(a))."""
    return {
        "record_type": "consent",
        "customer_id": body["customer_id"],
        "purpose_id": choice["purpose_id"],
        "category_id": choice["category_id"],
        "fields": choice["fields"],
        "action": choice["action"],
        "notice_version": body["notice_version"],
        "notice_sha256": notice_sha256,
        "language": body["language"],
        "channel": body["channel"],
        "recorded_at": recorded_at,
        # The API gateway's own reference for the request: the same value is in its access
        # log, so the record can be matched to who called and from where.
        "request_ref": request_ref,
        "caller": caller,
    }


def delivery_record(body: dict, notice_sha256: str, request_ref: str, caller: str,
                    recorded_at: str) -> dict:
    """The record that the current notice was delivered to a person who consented before the
    Act's obligations began (Section 5(2)). No message is sent by this build; in a company the
    messaging system would call the service once the message is delivered."""
    return {
        "record_type": "notice_delivered",
        "customer_id": body["customer_id"],
        "purpose_id": "notice",
        "action": "delivered",
        "notice_version": body["notice_version"],
        "notice_sha256": notice_sha256,
        "language": body["language"],
        "channel": body["channel"],
        "recorded_at": recorded_at,
        "request_ref": request_ref,
        "caller": caller,
    }


def receipt_key(record: dict) -> str:
    """Where the locked copy of a record is kept in the records bucket:
    consents/<customer>/<date>/<request>-<purpose>.json, or notice-deliveries/... ."""
    folder = "consents" if record["record_type"] == "consent" else "notice-deliveries"
    day = record["recorded_at"][:10]
    return (f"{folder}/{record['customer_id']}/{day}/"
            f"{record['request_ref']}-{record['purpose_id']}.json")


def ledger_item(record: dict, key: str, version_id: str, sha256: str) -> dict:
    """The ledger row for a record: the fields a search needs, and the location and fingerprint
    of the locked copy. The ledger is the index; the locked copy is the proof. If anyone later
    changes the row, the proof tool finds that it no longer matches the locked copy."""
    return {
        "customer_id": record["customer_id"],
        # Sort key: time first, so a customer's records come back in the order they were made.
        "record_key": f"{record['recorded_at']}#{record['request_ref']}#{record['purpose_id']}",
        "record_type": record["record_type"],
        "purpose_id": record["purpose_id"],
        "action": record["action"],
        "notice_version": record["notice_version"],
        "language": record["language"],
        "channel": record["channel"],
        "recorded_at": record["recorded_at"],
        "request_ref": record["request_ref"],
        "receipt_key": key,
        "receipt_version_id": version_id,
        "receipt_sha256": sha256,
    }


# The ledger fields that must equal the locked copy. tools/consent_proof.py compares them.
MATCHED_FIELDS = ("customer_id", "record_type", "purpose_id", "action", "notice_version",
                  "language", "channel", "recorded_at", "request_ref")
