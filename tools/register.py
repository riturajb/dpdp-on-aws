"""Load and check the personal data register.

Each problem is reported in plain English with the provision it relates to.
A FAIL stops a release. A WARN must be read and decided by a person.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_REGISTER = Path(__file__).resolve().parent.parent / "register" / "personal-data-register.yaml"
ALLOWED_BASES = {"consent"} | {f"s7({c})" for c in "abcdefghi"}
RETENTION_RULES = {"after_account_closure", "after_record", "until_withdrawn"}
BASIS_LABEL = {"consent": "Consent (Section 6)"} | {f"s7({c})": f"Legitimate use, Section 7({c})" for c in "abcdefghi"}


@dataclass
class Finding:
    """One problem found in the register: its level, the provision it relates to, and a message."""
    level: str      # "FAIL" or "WARN"
    provision: str  # e.g. "Section 4"
    message: str

    def __str__(self) -> str:
        return f"{self.level} [{self.provision}] {self.message}"


def load(path: str | Path = DEFAULT_REGISTER) -> dict:
    """Read the register file (YAML) into a dictionary."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check(reg: dict) -> list[Finding]:
    """Check the register on its own, without looking at AWS.

    Rules: every vendor has a contract clause (Section 8(2), Rule 6(1)(f)); vendors outside India
    are flagged for review (Section 16); every category has a notice description (Section 5(1)),
    known stores (Section 8(1)), a purpose with a valid legal basis (Section 4), and a retention
    rule with its legal reason (Section 8(7), Rule 8(3)).
    """
    out: list[Finding] = []
    stores = {s["id"] for s in reg.get("stores", [])}
    vendors = {v["id"]: v for v in reg.get("vendors", [])}

    for v in vendors.values():
        if not str(v.get("contract_clause", "")).strip():
            out.append(Finding("FAIL", "Section 8(2) and Rule 6(1)(f)",
                               f"Vendor '{v['id']}' has no contract clause recorded."))
        if str(v.get("location", "")).strip().lower() != "india":
            out.append(Finding("WARN", "Section 16",
                               f"Vendor '{v['id']}' is outside India ({v.get('location')}). "
                               "Confirm that no Government restriction applies to that country."))

    for c in reg.get("data_categories", []):
        cid = c.get("id", "<no id>")
        if not str(c.get("notice_description", "")).strip():
            out.append(Finding("FAIL", "Section 5(1) and Rule 3(b)",
                               f"Category '{cid}' has no description for the notice."))
        for s in c.get("stores", []):
            if s not in stores:
                out.append(Finding("FAIL", "Section 8(1)", f"Category '{cid}' names an unknown store '{s}'."))
        if not c.get("stores"):
            out.append(Finding("FAIL", "Section 8(1)", f"Category '{cid}' does not say where it is stored."))

        purposes = c.get("purposes") or []
        if not purposes:
            out.append(Finding("FAIL", "Section 4", f"Category '{cid}' has no purpose recorded."))
        for p in purposes:
            what = p.get("purpose") or "<no purpose text>"
            basis = p.get("legal_basis")
            if not basis:
                out.append(Finding("FAIL", "Section 4",
                                   f"Category '{cid}', purpose '{what}' has no legal basis. "
                                   "Record consent or the clause of Section 7 before this data is used."))
            elif basis not in ALLOWED_BASES:
                out.append(Finding("FAIL", "Section 4",
                                   f"Category '{cid}', purpose '{what}' has an invalid legal basis '{basis}'."))
            for v in p.get("shared_with") or []:
                if v not in vendors:
                    out.append(Finding("FAIL", "Section 8(2)",
                                       f"Category '{cid}' is shared with '{v}', which is not in the vendor list."))

        r = c.get("retention") or {}
        if r.get("rule") not in RETENTION_RULES or not str(r.get("legal_reason", "")).strip():
            out.append(Finding("FAIL", "Section 8(7) and Rule 8(3)",
                               f"Category '{cid}' has no retention rule with a legal reason."))
        elif r.get("rule") != "until_withdrawn" and not r.get("days"):
            out.append(Finding("FAIL", "Section 8(7) and Rule 8(3)",
                               f"Category '{cid}' has a retention rule without a number of days."))
        elif r.get("confirmed") is False:
            out.append(Finding("WARN", "Section 8(7)",
                               f"Category '{cid}': retention period not yet confirmed against the source law "
                               f"({r.get('legal_reason')})."))
    return out


def store_names(reg: dict, account_id: str) -> dict[str, str]:
    """Map each store id to its real resource name in an account."""
    return {s["id"]: s["name"].format(account_id=account_id) for s in reg["stores"]}
