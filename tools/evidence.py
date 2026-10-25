"""Write one evidence record for a control test.

Each record states the control, the time (IST), what was attempted, what the system
answered, the outcome, the Git commit of the code that ran the test, and a SHA-256
checksum of the record itself. Records go to the locked evidence bucket when a
bucket is given, otherwise to the local folder evidence/ (ignored by Git).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent


def _commit() -> str:
    """The Git commit of the code that ran the test, so a result can be traced to its exact code."""
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return sha + (" (with uncommitted changes)" if dirty else "")
    except Exception:
        return "not in a Git repository"


def record(control: str, test: str, attempted: str, response: str, outcome: str,
           session=None, bucket: str | None = None, account_folder: str | None = None) -> dict:
    """Build the record, add its checksum, and store it (bucket if given, otherwise evidence/)."""
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    rec = {
        "control": control,
        "test": test,
        "time": now.isoformat(timespec="seconds"),
        "attempted": attempted,
        "response": response,
        "outcome": outcome,
        "commit": _commit(),
    }
    rec["sha256"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    body = json.dumps(rec, indent=2)
    folder = account_folder or os.environ.get("DPDP_ACCOUNT_FOLDER", "local")
    key = f"{folder}/{now:%Y-%m-%d}/{control}/{test}-{now:%H%M%S}.json"

    bucket = bucket or os.environ.get("DPDP_EVIDENCE_BUCKET")
    if bucket and session is not None:
        # A checksum header is required when writing to an Object Lock bucket.
        resp = session.client("s3").put_object(Bucket=bucket, Key=key, Body=body.encode(),
                                               ContentType="application/json", ChecksumAlgorithm="SHA256")
        rec["stored_at"] = f"s3://{bucket}/{key}"
        rec["version_id"] = resp.get("VersionId")
    else:
        path = ROOT / "evidence" / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        rec["stored_at"] = str(path)
    return rec


def verify(rec: dict) -> bool:
    """Recompute the checksum of a record read back from storage."""
    body = {k: v for k, v in rec.items() if k not in ("sha256", "stored_at", "version_id")}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() == rec.get("sha256")
