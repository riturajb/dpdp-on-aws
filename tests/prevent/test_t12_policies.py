"""T12: the plan-check rules allow a compliant plan and stop each kind of non-compliant change.

Control:          DPDP-Act-S8(1), DPDP-Rule-6(1)(b), DPDP-Rule-6(1)(d), DPDP-Rule-6(1)(e)
What is checked:  The unit tests in policies/rego pass (conftest verify). A realistic compliant
                  plan passes the rules; a realistic non-compliant plan is stopped, with one
                  message for each provision: s.8(1), Rule 6(1)(b), 6(1)(d), 6(1)(e) and the
                  Mumbai-only rule.
Pass means:       The rules work as written, before they are trusted with real changes.
Fail means:       A rule could let a non-compliant change through, or block a compliant one.
Evidence stored:  Locally (offline).
Who runs it:      Anyone, with no AWS access; also GitHub Actions on every pull request.
                  Needs conftest (scripts/install_conftest.sh).
When:             Release 3, Steps 2 and 7; after any change to policies/rego.
Changes AWS:      No.
"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = ["[s.8(1)]", "[R.6(1)(b)]", "[R.6(1)(d)]", "[R.6(1)(e)]", "[Mumbai only]"]


def _conftest() -> str:
    found = shutil.which("conftest") or str(Path.home() / ".local/bin/conftest")
    assert Path(found).exists(), "conftest is not installed. Run scripts/install_conftest.sh"
    return found


def _run(*args) -> subprocess.CompletedProcess:
    return subprocess.run([_conftest(), *args, "--no-color"], cwd=ROOT, capture_output=True, text=True)


def _check_plan(name: str) -> subprocess.CompletedProcess:
    return _run("test", f"tests/fixtures/plans/{name}.json", "--policy", "policies/rego",
                "--data", "register/personal-data-register.yaml")


def test_t12_policies(record):
    # The rules' own unit tests, in policies/rego/prevent_test.rego.
    verify = _run("verify", "--policy", "policies/rego")
    assert verify.returncode == 0, verify.stdout + verify.stderr

    # A compliant plan passes; a non-compliant plan is stopped once for each provision.
    good = _check_plan("compliant")
    bad = _check_plan("noncompliant")
    missing = [tag for tag in EXPECTED if tag not in bad.stdout]
    ok = good.returncode == 0 and bad.returncode != 0 and not missing
    response = (f"unit tests: {verify.stdout.strip().splitlines()[-1] if verify.stdout.strip() else 'passed'}; "
                f"compliant plan exit code {good.returncode}; non-compliant plan exit code {bad.returncode}; "
                f"provisions not reported: {', '.join(missing) or 'none'}")
    record("DPDP-Act-S8(1)", "t12-plan-check-rules", "Run the plan-check rules against their unit tests and two plans",
           response, "PASS" if ok else "FAIL", account="offline")
    assert ok, response + "\n" + good.stdout + bad.stdout
