"""Load and check the AI register (register/ai-register.yaml).

Each problem is reported in plain English with the provision or source it relates to.
A FAIL stops a release. A WARN is an open item: it must be closed, or accepted in writing by
the role that owns the decision, before the entry moves from planned to in_development.

What:        Checks every AI system, model and staff AI tool in the AI register, and checks the
             AI register against the personal data register:
               - each AI system has an accountable role from the RACI, a purpose, a risk tier,
                 an impact assessment that exists, and an independent validator;
               - every category of personal data it uses is in the personal data register, and
                 no children's data is used;
               - every tool says whether it reads or changes something and whether it is
                 allowed; a tool that changes something needs a person's approval, or a
                 recorded reason why not; a forbidden tool needs a recorded reason;
               - prompts are masked before the model and before logging, model invocation
                 logging (which keeps unmasked prompts) is off, traces are kept for a year,
                 a customer is told she is talking to an AI and can ask for a person, and a
                 named role can suspend the system;
               - every model has the inventory fields of the RBI draft guidance, runs only in
                 India through an India inference profile, and is validated by someone other
                 than its owner;
               - every staff AI tool has a status, an owner and a rule; one approved for personal
                 data names a provider in the vendor list of the personal data register;
               - an open item (a purpose or category not yet in the personal data register) is a
                 WARN only while the system is planned; once it is in development or live, it
                 is a FAIL.
Why:         DPDP Act s.4 (lawful purpose), s.8(1) (the company answers for all processing,
             including by AI systems and their providers), s.8(5) and Rule 6(1) (security
             safeguards, logs kept a year), s.9 (children). RBI draft guidance on model risk
             management (24 June 2026, not final): model inventory, tiering, independent
             validation, human oversight, the ability to suspend, disclosure to customers.
Who runs it: Nobody directly. A library used by ai_register_check.py and tests T21 and T22.
When:        AI governance companion release (v0.5.1) onwards; Releases 12 and 13 build on it.
Reads:       register/ai-register.yaml and register/personal-data-register.yaml.
Writes:      Nothing.
Changes AWS: No.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tools.register import Finding

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AI_REGISTER = ROOT / "register" / "ai-register.yaml"

SYSTEM_STATUS = {"planned", "in_development", "live", "retired"}
STAFF_STATUS = {"allowed_without_personal_data", "approved", "planned", "not_allowed", "needs_approval"}
RISK_TIERS = {"high", "medium", "low"}
EFFECTS = {"read", "change"}
LOG_YEAR = 365            # Rule 6(1)(e): logs kept for one year
MODEL_FIELDS = ("owner_role", "developer", "validator_role", "approver_role", "risk_tier",
                "intended_use", "dependencies", "status")


def load(path: str | Path = DEFAULT_AI_REGISTER) -> dict:
    """Read the AI register file (YAML) into a dictionary."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or value == []


def check(ai: dict, pdr: dict, root: Path = ROOT) -> list[Finding]:
    """Check the AI register `ai` against the personal data register `pdr`.

    `root` is the folder that paths in the register (the impact assessment) are relative to."""
    out: list[Finding] = []
    roles = set(ai.get("roles") or [])
    regions = set(ai.get("allowed_regions") or [])
    prefixes = tuple(ai.get("allowed_profile_prefixes") or [])
    categories = {c["id"]: c for c in pdr.get("data_categories", [])}
    purposes = {p.get("id") for c in pdr.get("data_categories", []) for p in c.get("purposes", [])}
    vendors = {v["id"] for v in pdr.get("vendors", [])}
    models = {m.get("id"): m for m in ai.get("models") or []}

    def fail(where, msg):
        out.append(Finding("FAIL", where, msg))

    def warn(where, msg):
        out.append(Finding("WARN", where, msg))

    def role_ok(value, what, where="Section 8(1)"):
        if _blank(value):
            fail(where, f"{what} has no role recorded.")
        elif value not in roles:
            fail(where, f"{what} names '{value}', which is not a role in the RACI.")

    # --- AI systems -----------------------------------------------------------------------
    for s in ai.get("systems") or []:
        sid = s.get("id", "<no id>")
        name = f"AI system '{sid}'"
        if s.get("status") not in SYSTEM_STATUS:
            fail("Section 8(1)", f"{name} has no valid status ({sorted(SYSTEM_STATUS)}).")
        if _blank(s.get("description")):
            fail("Section 4", f"{name} does not say what it is for.")
        role_ok(s.get("accountable_role"), f"{name}: the accountable role")
        if s.get("risk_tier") not in RISK_TIERS:
            fail("RBI draft MRM: tiering", f"{name} has no risk tier ({sorted(RISK_TIERS)}).")

        # Personal data: everything used must be known to the personal data register.
        pd = s.get("personal_data") or {}
        for cid in pd.get("categories") or []:
            if cid not in categories:
                fail("Section 8(1)", f"{name} uses category '{cid}', which is not in the personal data register.")
            elif categories[cid].get("children"):
                fail("Section 9", f"{name} uses children's data ('{cid}'). Not allowed in this build.")
        for pid in pd.get("purposes") or []:
            if pid not in purposes:
                fail("Section 4", f"{name} relies on purpose '{pid}', which is not in the personal data register.")
        # An open item is allowed only while the system is planned: before anything is built.
        planned = s.get("status") == "planned"
        for p in pd.get("planned_purposes") or []:
            (warn if planned else fail)(
                "Section 4", f"{name}: purpose '{p.get('id')}' is not in the personal data register yet. "
                             f"{' '.join(str(p.get('why', '')).split())}")
        for c in pd.get("planned_categories") or []:
            (warn if planned else fail)(
                "Section 8(1)", f"{name}: category '{c.get('id')}' is not in the personal data register yet. "
                                f"{' '.join(str(c.get('why', '')).split())}")
        if s.get("children") is not False:
            fail("Section 9", f"{name} must state children: false (children's data is out of scope).")

        # Model.
        mid = s.get("model")
        if mid not in models:
            fail("RBI draft MRM: inventory", f"{name} uses model '{mid}', which is not in the model inventory.")
        elif sid not in (models[mid].get("used_by") or []):
            fail("RBI draft MRM: inventory", f"{name} is not listed under 'used_by' of model '{mid}'.")
        elif not planned and models[mid].get("status") == "planned":
            state = str(s.get("status")).replace("_", " ")
            fail("RBI draft MRM: inventory", f"{name} is {state}, but model '{mid}' is still planned.")

        # Tools: what each may do, and who approves changes.
        for t in s.get("tools") or []:
            tid = f"{name}, tool '{t.get('id', '<no id>')}'"
            if t.get("effect") not in EFFECTS:
                fail("Section 8(5)", f"{tid} does not say whether it reads or changes something.")
            if t.get("allowed") not in (True, False):
                fail("Section 8(5)", f"{tid} has no decision: allowed must be true or false.")
                continue
            for cid in t.get("reads") or []:
                if cid not in categories:
                    fail("Section 8(1)", f"{tid} reads '{cid}', which is not in the personal data register.")
                elif t["allowed"] and cid not in (pd.get("categories") or []):
                    fail("Section 4", f"{tid} reads '{cid}', which the system does not list among the data it uses.")
            if not t["allowed"]:
                if _blank(t.get("why_forbidden")):
                    fail("Section 8(1)", f"{tid} is forbidden without a recorded reason.")
                continue
            if t.get("reads") and t.get("scope") != "signed_in_customer_only":
                fail("Section 8(5)", f"{tid} reads personal data but is not limited to the signed-in customer.")
            if t.get("effect") == "change":
                approval = t.get("human_approval")
                if approval == "required":
                    if _blank(t.get("approver")):
                        fail("RBI draft MRM: human oversight", f"{tid} needs approval but names no approver.")
                elif approval == "not_required":
                    if _blank(t.get("why_no_approval")):
                        fail("RBI draft MRM: human oversight",
                             f"{tid} changes something without a person's approval and gives no reason.")
                else:
                    fail("RBI draft MRM: human oversight",
                         f"{tid} changes something and does not say whether a person must approve.")

        # Controls.
        c = s.get("controls") or {}
        if c.get("masking_before_model") is not True:
            fail("Rule 6(1)(a)", f"{name}: personal data must be masked before it reaches the model.")
        if c.get("masking_before_logging") is not True:
            fail("Rule 6(1)(a)", f"{name}: personal data must be masked before it is logged.")
        if c.get("model_invocation_logging") not in ("off", False):
            fail("Rule 6(1)(a)", f"{name}: model invocation logging keeps unmasked prompts; it must be off.")
        if not isinstance(c.get("trace_retention_days"), int) or c["trace_retention_days"] < LOG_YEAR:
            fail("Rule 6(1)(e)", f"{name}: traces must be kept for at least {LOG_YEAR} days.")
        if _blank(c.get("customer_check")):
            fail("Section 8(5)", f"{name}: no rule records how the customer is checked outside the model.")
        if s.get("customer_facing"):
            if c.get("ai_disclosure") is not True:
                fail("RBI draft MRM: disclosure", f"{name} is customer-facing and must tell people it is an AI.")
            if c.get("human_handoff") is not True:
                fail("RBI draft MRM: disclosure", f"{name} is customer-facing and must offer a person on request.")
        ks = c.get("kill_switch") or {}
        role_ok(ks.get("decides"), f"{name}: the kill switch", "RBI draft MRM: suspension")
        role_ok(ks.get("restart_needs"), f"{name}: restarting after suspension", "RBI draft MRM: suspension")
        if _blank(ks.get("how")):
            fail("RBI draft MRM: suspension", f"{name}: the kill switch does not say how it works.")

        # Impact assessment and validation.
        ia = s.get("impact_assessment")
        if _blank(ia) or not (root / ia).exists():
            fail("Section 8(1)", f"{name}: impact assessment '{ia}' not found.")
        v = s.get("validation") or {}
        if v.get("independent") is not True:
            fail("RBI draft MRM: validation", f"{name}: validation must be independent of the system's owner.")
        role_ok(v.get("validator_role"), f"{name}: the validator", "RBI draft MRM: validation")
        if v.get("validator_role") == s.get("accountable_role"):
            fail("RBI draft MRM: validation", f"{name}: the validator cannot be the accountable role.")
        if v.get("status") != "passed":
            state = str(v.get("status") or "not recorded").replace("_", " ")
            if s.get("status") == "live":
                fail("RBI draft MRM: validation", f"{name} is live without a passed validation.")
            else:
                warn("RBI draft MRM: validation", f"{name}: validation {state}; required before deployment.")

    # --- Models ---------------------------------------------------------------------------
    for mid, m in models.items():
        name = f"Model '{mid}'"
        for field in MODEL_FIELDS:
            if _blank(m.get(field)):
                fail("RBI draft MRM: inventory", f"{name} has no '{field}'.")
        for field in ("owner_role", "validator_role", "approver_role"):
            if not _blank(m.get(field)) and m.get(field) not in roles:
                fail("RBI draft MRM: inventory", f"{name}: '{field}' names '{m.get(field)}', not a role in the RACI.")
        if not _blank(m.get("owner_role")) and m.get("validator_role") == m.get("owner_role"):
            fail("RBI draft MRM: validation", f"{name}: the validator cannot be the owner.")
        bad = [r for r in m.get("regions") or [] if r not in regions]
        if not m.get("regions") or bad:
            fail("Section 16 (design choice: India only)",
                 f"{name} may process data in {bad or 'unstated regions'}; allowed: {sorted(regions)}.")
        profile = str(m.get("inference_profile") or "")
        if m.get("source") == "third_party" and not profile.startswith(prefixes):
            fail("Section 16 (design choice: India only)",
                 f"{name} uses '{profile or 'no profile'}'; only profiles starting {list(prefixes)} stay in India.")
        if m.get("vendor") not in vendors:
            if m.get("status") == "planned":
                warn("Section 8(2) and Rule 6(1)(f)",
                     f"{name}: provider '{m.get('vendor')}' is not in the vendor list of the personal data "
                     "register yet. Add it, with its contract clause, before the build.")
            else:
                fail("Section 8(2) and Rule 6(1)(f)",
                     f"{name}: provider '{m.get('vendor')}' must be in the vendor list before use.")
        if _blank(m.get("provider_data_terms")):
            fail("Section 8(2)", f"{name}: the provider's terms on training and retention are not recorded.")

    # --- Staff AI tools -------------------------------------------------------------------
    for t in ai.get("staff_tools") or []:
        name = f"Staff AI tool '{t.get('id', '<no id>')}'"
        if t.get("status") not in STAFF_STATUS:
            fail("Section 8(5)", f"{name} has no valid status ({sorted(STAFF_STATUS)}).")
        role_ok(t.get("owner_role"), f"{name}: the owner")
        if _blank(t.get("rule")) or _blank(t.get("enforced_by")):
            fail("Section 8(5)", f"{name} needs a rule and how it is enforced.")
        if t.get("status") == "approved" and t.get("vendor") not in vendors:
            fail("Section 8(2) and Rule 6(1)(f)",
                 f"{name} is approved for personal data, so its provider must be in the vendor list of "
                 "the personal data register, with its contract clause.")
    return out
