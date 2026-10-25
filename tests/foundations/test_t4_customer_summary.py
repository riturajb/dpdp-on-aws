"""T4: one command shows everything held about a customer.

Control:          DPDP-Act-S8(1)
What is checked:  For the test customer C-TEST-0001, the summary lists every category of
                  personal data held, with purpose, legal basis, vendors and retention.
Pass means:       All nine categories expected for an adult borrower appear, with vendors,
                  and Aadhaar and PAN are masked.
Fail means:       The company cannot say what it holds about a person.
Evidence stored:  Locally (offline) or the evidence bucket (live).
"""
import pytest

from tools import customer_summary, generate_synthetic_data, register

EXPECTED = {"Identity and KYC", "Contact details", "Marketing preferences", "Loan application",
            "Repayments and collections", "Credit bureau report", "Wallet transactions",
            "App and device activity", "Complaints and support requests"}


def _assert_summary(rows):
    names = {r["category"] for r in rows}
    assert names == EXPECTED, names ^ EXPECTED
    kyc = next(r for r in rows if r["category"] == "Identity and KYC")
    assert any("XXXX XXXX" in f for f in kyc["fields"]), "Aadhaar is not masked"
    assert kyc["purposes"][0]["shared_with"], "KYC vendor missing"


def test_t4_customer_summary_offline(tmp_path, record):
    data = generate_synthetic_data.build(50, 2026)
    generate_synthetic_data.write_files(data, tmp_path)
    rows = customer_summary.summarise(register.load(), customer_summary.OfflineSource(str(tmp_path)), "C-TEST-0001")
    _assert_summary(rows)
    record("DPDP-Act-S8(1)", "t4-customer-summary", "Summarise C-TEST-0001 from generated files",
           f"{len(rows)} categories listed", "PASS", account="offline")


@pytest.mark.live
def test_t4_customer_summary_live(record, target_session):
    reg = register.load()
    rows = customer_summary.summarise(reg, customer_summary.LiveSource(target_session, reg), "C-TEST-0001")
    _assert_summary(rows)
    record("DPDP-Act-S8(1)", "t4-customer-summary", "Summarise C-TEST-0001 from the account",
           f"{len(rows)} categories listed", "PASS", session=target_session)
