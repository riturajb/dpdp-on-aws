"""Check the personal data register, and optionally compare it with an AWS account.

  python tools/register_check.py                         # the register on its own
  python tools/register_check.py --register FILE         # another register file
  python tools/register_check.py --live --profile dpdp-workload-eng
                                                         # also compare with the account

Exit code 0 = no FAIL. Exit code 1 = at least one FAIL.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import register  # noqa: E402


def compare_with_account(reg: dict, session) -> list[register.Finding]:
    """Every store in the register must exist in the account, and every resource tagged
    DataClass=personal must be in the register."""
    out = []
    tagging = session.client("resourcegroupstaggingapi")
    found = {}
    for page in tagging.get_paginator("get_resources").paginate(
            TagFilters=[{"Key": "DataClass", "Values": ["personal"]}]):
        for res in page["ResourceTagMappingList"]:
            tags = {t["Key"]: t["Value"] for t in res.get("Tags", [])}
            found[tags.get("RegisterStore", "<no RegisterStore tag>")] = res["ResourceARN"]
    declared = {s["id"] for s in reg["stores"]}
    for sid, arn in sorted(found.items()):
        if sid not in declared:
            out.append(register.Finding("FAIL", "Section 8(1)",
                                        f"{arn} holds personal data but is not in the register (tag '{sid}')."))
    for sid in sorted(declared - set(found)):
        out.append(register.Finding("FAIL", "Section 8(1)",
                                    f"Store '{sid}' is in the register but was not found in the account."))
    return out


def main(argv=None) -> int:
    """Run the checks, print each finding, and return 1 if any FAIL was found (used by CI)."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--register", default=str(register.DEFAULT_REGISTER))
    ap.add_argument("--live", action="store_true", help="also compare with the AWS account")
    ap.add_argument("--profile", help="AWS CLI profile for --live")
    args = ap.parse_args(argv)

    reg = register.load(args.register)
    findings = register.check(reg)
    if args.live:
        import boto3
        findings += compare_with_account(reg, boto3.Session(profile_name=args.profile, region_name="ap-south-1"))

    fails = [f for f in findings if f.level == "FAIL"]
    warns = [f for f in findings if f.level == "WARN"]
    print(f"Register: {args.register}")
    print(f"Categories: {len(reg.get('data_categories', []))}, stores: {len(reg.get('stores', []))}, "
          f"vendors: {len(reg.get('vendors', []))}")
    for f in fails + warns:
        print(f"  {f}")
    print(f"Result: {'FAIL' if fails else 'PASS'} ({len(fails)} failures, {len(warns)} warnings to review)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
