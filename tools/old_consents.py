"""Give the notice to customers who consented before the Act's obligations began (Section 5(2)).

  python tools/old_consents.py --profile dpdp-workload-eng            # report only
  python tools/old_consents.py --profile dpdp-workload-eng --send     # record deliveries
  add --compact for short lines

What:        Lists the customers whose consent was given before the notice existed: every open
             adult account in the model company. For each, it looks in the consent ledger for a
             record that the current notice was delivered, or that the customer has since given
             consent against the current notice. It reports how many are covered and how many are
             still waiting. With --send, it records a delivery for each customer still waiting,
             through the consent API, exactly as a messaging system would after sending the
             notice by SMS.
Why:         DPDP Act, Section 5(2): where a person consented before the date of commencement,
             the company must give her a notice "as soon as it is reasonably practicable",
             describing the data, the purpose, her rights and how to complain. It may continue
             the processing until she withdraws. The company must be able to show who has been
             given the notice and who has not, which is this report.
Who runs it: An engineer (PlatformEngineer, profile dpdp-workload-eng). Test T20 runs it.
When:        Release 4, Step 7. A company runs the campaign once its notice is approved, and the
             report until no one is left waiting.
Reads:       The customers table and the consent ledger.
Writes:      Nothing on the laptop.
Changes AWS: --send only: one locked record and one ledger row per customer notified. No message
             is sent to anyone: this build has no messaging vendor, and all customers are
             synthetic. Running it twice is safe: customers already covered are skipped.

Left out, and said so in the report:
  - closed accounts: what Fernleaf keeps after closure it keeps because other laws require it
    (Release 7), not on the basis of consent, so it treats Section 5(2) as not applying. This is
    the model company's reading; a company confirms its own with counsel;
  - teen wallet accounts: the notice goes to the parent, with verifiable parental consent
    (Section 9(1), Rule 10), in Release 6.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import consent_client, consent_proof  # noqa: E402

REGION = "ap-south-1"
CUSTOMERS = "dpdp-customers"


def customers(session) -> list[dict]:
    """Every customer row: only the fields this report needs (no names, no identifiers)."""
    table = session.resource("dynamodb").Table(CUSTOMERS)
    kw = {"ProjectionExpression": "customer_id, account_type, closed_on, opened_on"}
    rows = []
    while True:
        page = table.scan(**kw)
        rows += page["Items"]
        if "LastEvaluatedKey" not in page:
            return sorted(rows, key=lambda r: r["customer_id"])
        kw["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def split(rows: list[dict]) -> dict[str, list[str]]:
    """Sort customers into those the notice must reach and those left out, with the reason."""
    out = {"eligible": [], "closed": [], "teen": []}
    for r in rows:
        if r.get("account_type") == "teen":
            out["teen"].append(r["customer_id"])
        elif r.get("closed_on"):
            out["closed"].append(r["customer_id"])
        else:
            out["eligible"].append(r["customer_id"])
    return out


def covered(session, customer: str, version: str) -> bool:
    """True if the ledger shows the current notice reached this customer: a delivery record, or
    a consent given against it (the notice is shown before every consent)."""
    for row in consent_proof.ledger_rows(session, customer):
        if row.get("notice_version") == version:
            return True
    return False


def campaign(session, send: bool = False) -> dict:
    """Report, and with send=True record a delivery for everyone still waiting."""
    notice = consent_client.get_notice(session)
    version = notice["notice_version"]
    groups = split(customers(session))
    waiting = [c for c in groups["eligible"] if not covered(session, c, version)]
    sent, failed = [], []
    if send:
        for c in waiting:
            status, _ = consent_client.deliver(session, c, channel="sms", version=version)
            (sent if status == 201 else failed).append(c)
        waiting = [c for c in waiting if c not in sent]
    return {"notice_version": version, "eligible": len(groups["eligible"]),
            "covered": len(groups["eligible"]) - len(waiting), "waiting": waiting,
            "sent_now": len(sent), "failed": failed,
            "left_out": {"closed accounts": len(groups["closed"]),
                         "teen accounts (Release 6)": len(groups["teen"])}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--send", action="store_true", help="record a delivery for each one waiting")
    ap.add_argument("--compact", action="store_true", help="short lines, for narrow screens")
    args = ap.parse_args(argv)
    import boto3
    r = campaign(boto3.Session(profile_name=args.profile, region_name=REGION), send=args.send)
    if args.compact:
        print(f"Notice {r['notice_version']}")
        print(f"Customers who consented before: {r['eligible']}")
        if args.send:
            print(f"Notice recorded now:            {r['sent_now']}")
        print(f"Covered:                        {r['covered']}")
        print(f"Still waiting:                  {len(r['waiting'])}")
        print(f"Left out: {r['left_out']['closed accounts']} closed, "
              f"{r['left_out']['teen accounts (Release 6)']} teen (Release 6)")
    else:
        print(f"Section 5(2) campaign for notice {r['notice_version']} (synthetic customers)\n")
        print(f"  Open adult accounts, consent given before the notice: {r['eligible']}")
        if args.send:
            print(f"  Deliveries recorded in this run:                      {r['sent_now']}")
        print(f"  Covered (notice delivered, or consent given since):   {r['covered']}")
        print(f"  Still waiting:                                        {len(r['waiting'])}")
        for reason, n in r["left_out"].items():
            print(f"  Left out, {reason}: {n}")
        if r["failed"]:
            print(f"  FAILED for: {', '.join(r['failed'][:10])}")
        if r["waiting"] and not args.send:
            print("\nRun again with --send to record the deliveries.")
    return 0 if not r["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
