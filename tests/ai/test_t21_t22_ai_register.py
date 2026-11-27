"""T21 and T22: the AI register is complete, and an unsafe AI entry is stopped.

Control:          DPDP-Act-S8(1) (T21); DPDP-Act-S8(5) (T22)
What is checked:  T21: the AI register (register/ai-register.yaml) passes tools/ai_register.py
                  against the personal data register: every AI system has an owner, a purpose,
                  a risk tier, an impact assessment and an independent validator; every model
                  has the inventory fields of the RBI draft guidance and runs in India; every
                  staff AI tool has an owner and a rule. Open items (WARN) are allowed while an
                  entry is planned.
                  T22: six broken copies of the AI register must each fail, naming the provision:
                    1. the model reached through a profile that can process data outside India;
                    2. a tool that changes a loan with no rule on a person's approval;
                    3. a forbidden tool allowed, reading credit bureau data the system does not list;
                    4. model invocation logging switched on (it keeps unmasked prompts);
                    5. the accountable role validating its own system;
                    6. the system moved to in_development while a purpose it relies on is
                       still missing from the personal data register.
Pass means:       T21: no FAIL. T22: every broken copy produces the expected FAIL.
Fail means:       An AI system could use personal data, act or log in a way the company has not
                  decided, and nothing would stop the change before it is merged.
Evidence stored:  Locally in evidence/ (offline tests, also run in GitHub Actions).
Who runs it:      Anyone, with no AWS access; also GitHub Actions on every pull request.
When:             AI governance companion release (v0.5.1), Step 2; after every change to either
                  register.
Changes AWS:      No.
"""
import copy

from tools import ai_register, register


def _fails(ai):
    return [f for f in ai_register.check(ai, register.load()) if f.level == "FAIL"]


def _tool(ai, tool_id):
    return next(t for t in ai["systems"][0]["tools"] if t["id"] == tool_id)


def test_t21_ai_register_is_complete(record):
    findings = ai_register.check(ai_register.load(), register.load())
    fails = [str(f) for f in findings if f.level == "FAIL"]
    opened = [str(f) for f in findings if f.level == "WARN"]
    record("DPDP-Act-S8(1)", "t21-ai-register-is-complete",
           "Check the AI register against the personal data register",
           ("; ".join(fails) or "No failures") + f"; open items: {len(opened)}",
           "PASS" if not fails else "FAIL", account="offline")
    assert not fails, fails


def test_t22_unsafe_ai_entries_are_stopped(record):
    base = ai_register.load()
    cases = {}

    ai = copy.deepcopy(base)
    ai["models"][0]["inference_profile"] = "apac.anthropic.claude-sonnet-5"
    ai["models"][0]["regions"] = ["ap-south-1", "ap-southeast-1"]
    cases["model outside India"] = (ai, "Section 16")

    ai = copy.deepcopy(base)
    _tool(ai, "request_repayment_date_change").pop("human_approval")
    cases["change without approval rule"] = (ai, "RBI draft MRM: human oversight")

    ai = copy.deepcopy(base)
    _tool(ai, "get_credit_score")["allowed"] = True
    _tool(ai, "get_credit_score")["scope"] = "signed_in_customer_only"
    cases["credit bureau data not listed"] = (ai, "Section 4")

    ai = copy.deepcopy(base)
    ai["systems"][0]["controls"]["model_invocation_logging"] = "on"
    cases["unmasked prompts logged"] = (ai, "Rule 6(1)(a)")

    ai = copy.deepcopy(base)
    ai["systems"][0]["validation"]["validator_role"] = ai["systems"][0]["accountable_role"]
    cases["owner validates own system"] = (ai, "RBI draft MRM: validation")

    ai = copy.deepcopy(base)
    ai["systems"][0]["status"] = "in_development"
    cases["built before its purpose is recorded"] = (ai, "Section 4")

    results, missed = [], []
    for name, (ai, provision) in cases.items():
        hits = [f for f in _fails(ai) if f.provision.startswith(provision)]
        results.append(f"{name}: {'stopped [' + provision + ']' if hits else 'NOT stopped'}")
        if not hits:
            missed.append(name)
    record("DPDP-Act-S8(5)", "t22-unsafe-ai-entries-are-stopped",
           "Six unsafe changes to the AI register", "; ".join(results),
           "PASS" if not missed else "FAIL", account="offline")
    assert not missed, f"Not stopped: {missed}"
