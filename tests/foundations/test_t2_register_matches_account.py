"""T2: the register matches the stores that actually exist in the account.

Control:          DPDP-Act-S8(1)
What is checked:  Every store in the register exists, and every resource tagged
                  DataClass=personal is in the register.
Pass means:       No store holds personal data without the company knowing about it.
Fail means:       The register and the account disagree.
Evidence stored:  The evidence bucket for the target account.
"""
import pytest

from tools import register
from tools.register_check import compare_with_account


@pytest.mark.live
def test_t2_register_matches_account(record, target_session):
    findings = compare_with_account(register.load(), target_session)
    fails = [str(f) for f in findings if f.level == "FAIL"]
    record("DPDP-Act-S8(1)", "t2-register-matches-account",
           "Compare the register with resources tagged DataClass=personal",
           "; ".join(fails) or "Register and account match", "PASS" if not fails else "FAIL",
           session=target_session)
    assert not fails, fails
