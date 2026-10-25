"""T7: nobody signs in with stored passwords or access keys.

Control:          DPDP-Rule-6(1)(b)
What is checked:  The target account and the log archive account have no IAM users, so no
                  long-lived passwords or access keys. People sign in through IAM Identity Center
                  with multi-factor authentication.
Pass means:       No IAM users found.
Fail means:       Someone created a user with stored credentials.
Evidence stored:  The evidence bucket for the target account.
"""
import pytest

pytestmark = pytest.mark.live


@pytest.mark.parametrize("which", ["target", "log-archive"])
def test_t7_no_iam_users(record, which, target_session, logarchive_session):
    session = target_session if which == "target" else logarchive_session
    iam = session.client("iam")
    users = [u["UserName"] for page in iam.get_paginator("list_users").paginate() for u in page["Users"]]
    account = session.client("sts").get_caller_identity()["Account"]
    record("DPDP-Rule-6(1)(b)", f"t7-no-iam-users-{which}", f"List IAM users in account {account}",
           f"{len(users)} users: {', '.join(users) or 'none'}", "PASS" if not users else "FAIL",
           session=target_session)
    assert not users, users
