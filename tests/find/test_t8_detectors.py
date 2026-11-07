"""T8: the detectors find Indian identifiers, rate them correctly, and never expose a full value.

Control:          DPDP-Act-S8(1)
What is checked:  Aadhaar numbers with and without a correct Verhoeff check digit, PANs with a
                  valid and an invalid holder type, mobile numbers and email addresses are found
                  and rated high or medium; identifiers inside UUIDs and AWS account ids in ARNs
                  are not reported; masked values never contain the full identifier; and a scan
                  of the clean synthetic data reports no problems.
Pass means:       The scanner can be trusted to find identifiers without inventing them.
Fail means:       Discovery would miss personal data, or bury real findings in false alarms.
Evidence stored:  Locally (offline).
Who runs it:      Anyone, with no AWS access: pytest tests/find/test_t8_detectors.py
When:             Release 2, Step 1 and Step 6; after any change to tools/detectors.py.
Changes AWS:      No.
"""
from tools import detectors, discover, generate_synthetic_data, register, verhoeff


def _valid_aadhaar(body: str) -> str:
    """Make a 12-digit number that passes the Verhoeff check, as an issued Aadhaar would.
    It is built for the test and belongs to nobody."""
    return body + str(verhoeff.check_digit(body))


def test_t8_detectors(tmp_path, record):
    # One sample line with each case the scanner must handle:
    #   a number that passes the Aadhaar check (high) and the same number mistyped (medium);
    #   a PAN with holder type P (person, high) and one with an impossible holder type X (medium);
    #   a real-format mobile (high) and a synthetic +91-0000 number (medium); an email;
    #   a device UUID and an ARN, whose digit groups must NOT be read as Aadhaar numbers.
    real_like = _valid_aadhaar("23456789012")
    typo = real_like[:-1] + str((int(real_like[-1]) + 1) % 10)
    text = (f"Aadhaar {real_like[:4]} {real_like[4:8]} {real_like[8:]} and {typo}; "
            "PAN ABCPK1234Q and ABCXK1234Q; mobile 9876543210 and +91-0000-123456; "
            "mail asha.rao@example.com; device 3f6c1a2e-9b7d-4c1e-8a2b-345678901234; "
            "arn:aws:s3:ap-south-1:234567890123:bucket")
    got = {(m.identifier, m.confidence) for m in detectors.find(text)}
    assert ("aadhaar", "high") in got and ("aadhaar", "medium") in got, got
    assert ("pan", "high") in got and ("pan", "medium") in got, got
    assert ("mobile", "high") in got and ("mobile", "medium") in got, got
    assert ("email", "high") in got, got
    assert len([m for m in detectors.find(text) if m.identifier == "aadhaar"]) == 2, "UUID or ARN read as Aadhaar"
    # A report must never become a copy of the data: at most four digits of any value.
    for m in detectors.find(text):
        digits ="".join(ch for ch in m.masked if ch.isdigit())
        assert len(digits) <= 4, f"masked value shows too much: {m.masked}"

    # The clean synthetic data matches the register exactly, so a scan must find personal
    # data (the scanner works) and report no problem (the scanner does not raise false alarms).
    data = generate_synthetic_data.build(200, 2026)
    generate_synthetic_data.write_files(data, tmp_path)
    col, account = discover.scan_files(str(tmp_path))
    findings = discover.reconcile(col, register.load(), account)
    problems = [f for f in findings if f.verdict != "expected"]
    assert not problems, [(f.store_name, f.field, f.identifier) for f in problems]
    assert any(f.identifier == "aadhaar" and f.confidence == "medium" for f in findings), "synthetic Aadhaar not found"
    record("DPDP-Act-S8(1)", "t8-detectors", "Detect identifiers in sample text and in the clean synthetic data",
           f"{len(got)} identifier and confidence pairs found; {len(findings)} expected findings, 0 problems",
           "PASS", account="offline")
