"""T6: storage cannot be created outside the Mumbai region.

Control:          DPDP-Act-S16 (and RBI's direction that payment system data is stored only in India)
What is checked:  Signed in as PlatformEngineer of the target account, try to create an S3
                  bucket in Singapore (ap-southeast-1).
Pass means:       The request is refused by the organisation's guardrail.
Fail means:       Data could be stored outside India by mistake.
Evidence stored:  The evidence bucket for the target account.
"""
import uuid

import pytest

from tests.conftest import refused

pytestmark = pytest.mark.live


def test_t6_storage_outside_mumbai_is_refused(record, target_session):
    s3 = target_session.client("s3", region_name="ap-southeast-1")
    name = f"dpdp-region-test-{uuid.uuid4().hex[:12]}"
    ok, response = refused(lambda: s3.create_bucket(
        Bucket=name, CreateBucketConfiguration={"LocationConstraint": "ap-southeast-1"}))
    if not ok and "succeeded" in response:
        s3.delete_bucket(Bucket=name)
    record("DPDP-Act-S16", "t6-storage-outside-mumbai-is-refused",
           f"Create bucket {name} in ap-southeast-1 (Singapore)", response,
           "PASS" if ok else "FAIL", session=target_session)
    assert ok, response
