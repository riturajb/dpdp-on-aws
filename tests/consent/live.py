"""Values shared by the live consent tests (T18 to T20). Not a test file itself."""

# The synthetic test customer of Release 1. Every consent the tests record is for this customer.
CUSTOMER = "C-TEST-0001"


def expected_mode(target: str) -> str:
    """The lock mode of the consent records: COMPLIANCE in the workload account, where nobody
    can remove them early; GOVERNANCE in the sandbox, so that the clean-room copy can be
    removed (terraform/live/*/consent)."""
    return "COMPLIANCE" if target == "workload" else "GOVERNANCE"
