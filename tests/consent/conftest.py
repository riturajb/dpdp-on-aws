"""Set-up for the live consent tests (T18 to T20).

published: makes sure the notice that passes the check is the current notice in the target
           account (tools/notice.py publish), once per test run, before the first consent is
           sent. Publishing is safe to repeat: a version already published is not written
           again, and a new version is published only if the register changed.
"""
import pytest

from tools import notice, register


@pytest.fixture(scope="session")
def published(target_session) -> str:
    version, _ = notice.publish(target_session, notice.build(register.load()))
    return version
