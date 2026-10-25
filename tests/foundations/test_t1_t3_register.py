"""T1 and T3: the register is complete, and a data flow without a legal basis is blocked.

Control:          DPDP-Act-S4
What is checked:  Every category of personal data has a purpose, a legal basis, a store,
                  a retention rule with its legal reason, and a contract clause for each vendor.
Pass means:       The register passes; a copy with a flow that has no legal basis fails.
Fail means:       Personal data could be used without a recorded purpose or legal basis.
Evidence stored:  Locally in evidence/ (offline test, also run in GitHub Actions).
"""
from pathlib import Path

from tools import register

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "register_missing_basis.yaml"


def test_t1_register_is_complete(record):
    findings = register.check(register.load())
    fails = [str(f) for f in findings if f.level == "FAIL"]
    record("DPDP-Act-S4", "t1-register-is-complete", "Check the personal data register",
           "; ".join(fails) or "No failures", "PASS" if not fails else "FAIL", account="offline")
    assert not fails, fails


def test_t3_flow_without_legal_basis_is_blocked(record):
    findings = register.check(register.load(FIXTURE))
    section4 = [str(f) for f in findings if f.level == "FAIL" and f.provision == "Section 4"]
    record("DPDP-Act-S4", "t3-flow-without-legal-basis-is-blocked",
           "Add a data flow to a marketing partner with no legal basis",
           "; ".join(section4) or "Not blocked", "PASS" if section4 else "FAIL", account="offline")
    assert section4, "A flow without a legal basis was not blocked"
