"""Find Indian personal identifiers in text: Aadhaar, PAN, mobile numbers and email addresses.

What:        The pattern library behind the Release 2 scanner. A library, not a command:
             tools/discover.py and test T8 call it.
Why:         DPDP Act, section 8(1): a company is responsible for the personal data it
             processes, so it must know where that data is. AWS has no ready-made detector for
             Aadhaar or PAN numbers in DynamoDB or CloudWatch Logs, and Amazon Macie (S3 only)
             reports them only with a keyword such as "Aadhaar" close by.
Who runs it: Nobody directly. It runs inside discover.py, with whatever access that has.
When:        Release 2 onwards.
Reads:       The text it is given.   Writes: nothing.
Changes AWS: No.

Each match has a confidence:
  high    the value passes every validity check, so it could be a real, issued identifier
          (an Aadhaar number with a correct Verhoeff check digit, a PAN with a valid holder
          type, a mobile number starting 6 to 9)
  medium  the value has the right format but fails a validity check. That covers typing
          errors in real identifiers, test values, and all of this project's synthetic data,
          which is generated to fail these checks on purpose.

Both levels are reported. A mistyped Aadhaar number in a call-centre note is still a
customer's personal data, so a scanner that ignored medium matches would miss real problems.

Values are never returned in full: every match carries a masked form only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from tools import verhoeff

# A value must not run on from a letter, a digit or a hyphen on either side. This keeps the
# 12-character groups inside identifiers such as UUIDs, and account ids in names such as
# dpdp-bureau-reports-123456789012, from being read as Aadhaar numbers.
_B, _E = r"(?<![\w-])", r"(?![\w-])"

# Aadhaar: 12 digits, never starting with 0 or 1, written together or in groups of four
# separated by spaces or hyphens, as people type them in notes.
AADHAAR = re.compile(_B + r"([2-9]\d{3})[ -]?(\d{4})[ -]?(\d{4})" + _E)
# PAN: five letters, four digits, one letter. The fourth letter is the holder type.
PAN = re.compile(_B + r"([A-Z]{3})([A-Z])([A-Z])(\d{4})([A-Z])" + _E)
# Indian mobile: ten digits starting 6 to 9, with an optional +91 or 0 in front.
MOBILE = re.compile(r"(?<![\w-])(?:\+91[ -]?|0)?((?:[6-9]\d{9})|(?:[6-9]\d{4}[ -]\d{5}))" + _E)
# The synthetic customers have numbers such as +91-0000-123456, which no operator issues.
# They are reported as medium, so that a scan of the synthetic data still finds them.
MOBILE_SYNTHETIC = re.compile(r"\+91[ -]?(0\d{3}[ -]?\d{6})" + _E)
EMAIL = re.compile(r"(?<![\w.+-])([\w.+-]+)@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")

# Fourth character of a PAN: the type of holder (person, company, HUF, firm, AOP, trust,
# body of individuals, local authority, artificial juridical person, government).
PAN_HOLDER_TYPES = set("PCHFATBLJG")


@dataclass(frozen=True)
class Match:
    identifier: str   # aadhaar, pan, mobile, email
    confidence: str   # high or medium
    masked: str       # never the full value


# Masks keep no more than the last four characters, as UIDAI's masked Aadhaar does. They let a
# person recognise a record during an investigation without the report becoming a copy of it.
def mask_aadhaar(digits: str) -> str:
    return "XXXX XXXX " + digits[-4:]


def mask_pan(pan: str) -> str:
    return "XXXXX" + pan[5:9] + "X"


def mask_mobile(digits: str) -> str:
    return "XXXXXX" + digits[-4:]


def mask_email(local: str, domain: str) -> str:
    return local[:1] + "***@" + domain


def find(text: str, ignore: set[str] | None = None) -> list[Match]:
    """All identifiers in a piece of text. `ignore` holds 12-digit numbers known not to be
    personal data, such as the AWS account's own id."""
    ignore = ignore or set()
    out: list[Match] = []
    for m in AADHAAR.finditer(text):
        digits = "".join(m.groups())
        if digits in ignore or text[max(0, m.start() - 1):m.start()] == ":":
            continue  # an account id inside an ARN, such as arn:aws:s3:...:123456789012
        # Every issued Aadhaar number ends in a Verhoeff check digit. A number that fails the
        # check is a typing error, a test value or synthetic data: still reported, as medium.
        out.append(Match("aadhaar", "high" if verhoeff.is_valid(digits) else "medium", mask_aadhaar(digits)))
    for m in PAN.finditer(text):
        pan = "".join(m.groups())
        out.append(Match("pan", "high" if m.group(2) in PAN_HOLDER_TYPES else "medium", mask_pan(pan)))
    for m in MOBILE.finditer(text):
        digits = re.sub(r"\D", "", m.group(1))
        out.append(Match("mobile", "high", mask_mobile(digits)))
    for m in MOBILE_SYNTHETIC.finditer(text):
        digits = re.sub(r"\D", "", m.group(1))
        out.append(Match("mobile", "medium", mask_mobile(digits)))
    for m in EMAIL.finditer(text):
        out.append(Match("email", "high", mask_email(m.group(1), m.group(2))))
    return out
