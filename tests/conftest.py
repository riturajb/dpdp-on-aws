"""Shared test set-up.

Offline tests run everywhere, including GitHub Actions.
Live tests (marked 'live') need AWS sign-in and run only with:  pytest --live
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import evidence  # noqa: E402

DENIED = {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation", "OperationNotPermittedException"}


def _load_env():
    """Read config/local.env (bucket names, profiles, target) into the environment."""
    f = ROOT / "config" / "local.env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()   # the file always wins over the shell


_load_env()


def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", help="run tests against the AWS accounts")


def pytest_configure(config):
    config.addinivalue_line("markers", "live: needs AWS sign-in; runs only with --live")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live"):
        return
    skip = pytest.mark.skip(reason="live test: run with --live")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)


def env(name: str) -> str:
    """A required setting from config/local.env; stops the test with a clear message if missing."""
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} is not set. Copy config/local.env.example to config/local.env and fill it in.")
    return value


@pytest.fixture(scope="session")
def target() -> str:
    """workload for the live run, sandbox for the clean-room run before a release."""
    t = os.environ.get("DPDP_TARGET", "workload")
    assert t in ("workload", "sandbox"), "DPDP_TARGET must be workload or sandbox"
    return t


@pytest.fixture(scope="session")
def target_session(target):
    """Signed in to the target account as PlatformEngineer."""
    import boto3
    profile = env("DPDP_PROFILE_WORKLOAD" if target == "workload" else "DPDP_PROFILE_SANDBOX")
    return boto3.Session(profile_name=profile, region_name="ap-south-1")


@pytest.fixture(scope="session")
def logarchive_session():
    """Signed in to the log archive account as BreakGlassAdmin, the most powerful role there."""
    import boto3
    return boto3.Session(profile_name=env("DPDP_PROFILE_LOGARCHIVE"), region_name="ap-south-1")


@pytest.fixture
def record(request, target):
    """record(control, test, attempted, response, outcome, account='target'|'log-archive'|'offline')"""
    live = request.config.getoption("--live")

    def _record(control, test, attempted, response, outcome, account="target", session=None):
        if not live or account == "offline":
            return evidence.record(control, test, attempted, response, outcome)
        bucket = env("DPDP_EVIDENCE_LIVE_BUCKET" if target == "workload" else "DPDP_EVIDENCE_SANDBOX_BUCKET")
        folder = "dpdp-log-archive" if account == "log-archive" else f"dpdp-{target}"
        rec = evidence.record(control, test, attempted, response, outcome,
                              session=session, bucket=bucket, account_folder=folder)
        print(f"\n  evidence: {rec['stored_at']} (version {rec.get('version_id')})")
        return rec

    return _record


def refused(call):
    """Run an AWS call that must be refused. Returns (refused: bool, response text)."""
    from botocore.exceptions import ClientError
    try:
        call()
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", "")
        return code in DENIED, f"{code}: {msg}"[:300]
    return False, "The call succeeded. It should have been refused."
