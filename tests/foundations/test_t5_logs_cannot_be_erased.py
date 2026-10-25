"""T5: logs cannot be erased or weakened, even by an administrator.

Control:          DPDP-Rule-6(1)(e) (logs kept for one year) and DPDP-Rule-6(1)(c) (the trail keeps running)
What is checked:  Signed in as BreakGlassAdmin of the log archive account, try to delete a log
                  file (with and without a version id), shorten the bucket's retention, suspend
                  versioning, delete the bucket, and stop the organisation trail.
Pass means:       Every attempt is refused, and no delete marker is created.
Fail means:       An administrator could erase or weaken the access logs.
Evidence stored:  The evidence bucket, folder dpdp-log-archive.
"""
import pytest

from tests.conftest import env, refused

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def s3(logarchive_session):
    return logarchive_session.client("s3")


@pytest.fixture(scope="module")
def bucket():
    return env("DPDP_CLOUDTRAIL_BUCKET")


@pytest.fixture(scope="module")
def log_key(s3, bucket):
    resp = s3.list_objects_v2(Bucket=bucket, Prefix="AWSLogs/", MaxKeys=1)
    if not resp.get("KeyCount"):
        pytest.skip("No log file delivered yet. CloudTrail can take up to 15 minutes.")
    return resp["Contents"][0]["Key"]


def _check(record, session, control, test, attempted, call):
    ok, response = refused(call)
    record(control, test, attempted, response, "PASS" if ok else "FAIL", account="log-archive", session=session)
    assert ok, response


def test_t5a_delete_log_file(record, logarchive_session, s3, bucket, log_key):
    before = s3.list_object_versions(Bucket=bucket, Prefix=log_key)
    _check(record, logarchive_session, "DPDP-Rule-6(1)(e)", "t5a-delete-log-file",
           f"Delete s3://{bucket}/{log_key} without a version id",
           lambda: s3.delete_object(Bucket=bucket, Key=log_key))
    after = s3.list_object_versions(Bucket=bucket, Prefix=log_key)
    assert len(after.get("DeleteMarkers", [])) == len(before.get("DeleteMarkers", [])), "A delete marker was created"


def test_t5b_delete_log_file_version(record, logarchive_session, s3, bucket, log_key):
    version = s3.list_object_versions(Bucket=bucket, Prefix=log_key)["Versions"][0]["VersionId"]
    _check(record, logarchive_session, "DPDP-Rule-6(1)(e)", "t5b-delete-log-file-version",
           f"Delete version {version} of s3://{bucket}/{log_key}",
           lambda: s3.delete_object(Bucket=bucket, Key=log_key, VersionId=version))


def test_t5c_shorten_retention(record, logarchive_session, s3, bucket):
    _check(record, logarchive_session, "DPDP-Rule-6(1)(e)", "t5c-shorten-retention",
           f"Change the default retention of {bucket} to 1 day",
           lambda: s3.put_object_lock_configuration(Bucket=bucket, ObjectLockConfiguration={
               "ObjectLockEnabled": "Enabled", "Rule": {"DefaultRetention": {"Mode": "GOVERNANCE", "Days": 1}}}))


def test_t5d_suspend_versioning(record, logarchive_session, s3, bucket):
    _check(record, logarchive_session, "DPDP-Rule-6(1)(e)", "t5d-suspend-versioning",
           f"Suspend versioning on {bucket}",
           lambda: s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Suspended"}))


def test_t5e_delete_bucket(record, logarchive_session, s3, bucket):
    _check(record, logarchive_session, "DPDP-Rule-6(1)(e)", "t5e-delete-bucket",
           f"Delete the bucket {bucket}", lambda: s3.delete_bucket(Bucket=bucket))


def test_t5f_stop_the_trail(record, logarchive_session):
    trail = env("DPDP_TRAIL_ARN")
    ct = logarchive_session.client("cloudtrail")
    _check(record, logarchive_session, "DPDP-Rule-6(1)(c)", "t5f-stop-the-trail",
           f"Stop logging on {trail} from the log archive account",
           lambda: ct.stop_logging(Name=trail))
