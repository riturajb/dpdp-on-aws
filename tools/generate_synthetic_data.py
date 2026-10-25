"""Generate synthetic customers for Fernleaf Finance (fictional), the model lending and wallet company.

Nothing here is real:
  - Aadhaar numbers are 12 digits starting 2 to 9 and deliberately FAIL the Verhoeff
    check digit, so none can be an issued Aadhaar number.
  - PANs use 'X' as the fourth character, which is not a valid PAN holder type,
    so none can be an issued PAN.
  - Mobile numbers start +91-0000, which no Indian mobile number does.
  - Emails use example.com; IP addresses use the documentation ranges 203.0.113.0/24
    and 198.51.100.0/24.

  python tools/generate_synthetic_data.py --out data/            # write JSON files only
  python tools/generate_synthetic_data.py --out data/ --load --profile dpdp-workload-eng
                                                                 # also load into the account
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import register, verhoeff  # noqa: E402

FIRST = ["Aarav", "Vivaan", "Aditya", "Ishaan", "Arjun", "Ananya", "Diya", "Saanvi", "Meera", "Kavya",
         "Rohan", "Kabir", "Priya", "Neha", "Farhan", "Zoya", "Gurpreet", "Simran", "Lakshmi", "Venkat"]
LAST = ["Sharma", "Iyer", "Reddy", "Khan", "Das", "Patel", "Singh", "Nair", "Mukherjee", "Fernandes",
        "Gupta", "Rao", "Joshi", "Bhat", "Menon"]
CITIES = ["Pune", "Indore", "Kochi", "Jaipur", "Lucknow", "Nagpur", "Mysuru", "Bhopal", "Surat", "Guwahati"]
MERCHANTS = ["Grocery store", "Pharmacy", "Mobile recharge", "Bus ticket", "Bookshop", "Canteen", "Electricity bill"]
EVENTS = ["login", "view_balance", "view_loan", "pay_merchant", "update_profile", "logout"]
EMPLOYERS = ["Textile mill", "IT services firm", "Government school", "Hospital", "Retail chain", "Self-employed"]
IST = timezone(timedelta(hours=5, minutes=30))


def fake_aadhaar(rng: random.Random) -> str:
    """12 digits starting 2 to 9, with a last digit chosen to FAIL the Verhoeff check."""
    body = str(rng.randint(2, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(10))
    good = verhoeff.check_digit(body)
    bad = rng.choice([d for d in range(10) if d != good])
    number = body + str(bad)
    assert not verhoeff.is_valid(number)
    return number


def fake_pan(rng: random.Random, surname: str) -> str:
    """PAN format, but with 'X' as the holder-type letter, which no real PAN uses."""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ("".join(rng.choice(letters) for _ in range(3)) + "X" + surname[0].upper()
            + f"{rng.randint(0, 9999):04d}" + rng.choice(letters))


def iso(d) -> str:
    """Date or time as text in ISO format (2026-10-14)."""
    return d.isoformat()


def customer(rng, cid, *, teen=False, parent=None, closed=False, today=None):
    """One customer record. Teens (13 to 17) are linked to a parent and have no Aadhaar or PAN."""
    today = today or date(2026, 10, 14)
    first, last = rng.choice(FIRST), rng.choice(LAST)
    age = rng.randint(13, 17) if teen else rng.randint(21, 62)
    dob = today - timedelta(days=age * 365 + rng.randint(0, 364))
    opened = today - timedelta(days=rng.randint(60, 1500))
    c = {
        "customer_id": cid,
        "full_name": f"{first} {last}",
        "date_of_birth": iso(dob),
        "mobile": f"+91-0000-{rng.randint(0, 999999):06d}",
        "email": f"{first.lower()}.{cid.lower()}@example.com",
        "address": f"{rng.randint(1, 300)}, Synthetic Lane, {rng.choice(CITIES)}",
        "account_type": "teen" if teen else "adult",
        "opened_on": iso(opened),
        "closed_on": iso(today - timedelta(days=rng.randint(1, 50))) if closed else None,
        "marketing_opt_in": (not teen) and rng.random() < 0.6,
    }
    if teen:
        c["parent_customer_id"] = parent
    else:
        c["aadhaar_number"] = fake_aadhaar(rng)
        c["pan"] = fake_pan(rng, last)
    return c


def build(n: int, seed: int) -> dict:
    """Build the whole dataset. The same seed always gives the same data, so tests are repeatable.

    C-TEST-0001 always exists (adult borrower, overdue instalment, a support ticket);
    C-TEST-0002 is a teen linked to C-TEST-0001.
    """
    rng = random.Random(seed)
    today = date(2026, 10, 14)
    customers, loans, wallet, tickets, bureau, events = [], [], [], [], {}, {}

    ids = ["C-TEST-0001"] + [f"C-{i:06d}" for i in range(1, n)]
    for i, cid in enumerate(ids):
        teen = cid != "C-TEST-0001" and rng.random() < 0.12
        parent = rng.choice([c["customer_id"] for c in customers if c["account_type"] == "adult"]) if teen and customers else None
        c = customer(rng, cid, teen=teen and parent is not None, parent=parent,
                     closed=(cid != "C-TEST-0001" and rng.random() < 0.08), today=today)
        if cid == "C-TEST-0001":
            c.update(full_name="Test Customer One", email="test.customer.one@example.com", marketing_opt_in=True)
        customers.append(c)

        if c["account_type"] == "adult" and (cid == "C-TEST-0001" or rng.random() < 0.55):
            disbursed = today - timedelta(days=rng.randint(30, 700))
            overdue = rng.choice([0, 0, 0, 15, 45]) if cid != "C-TEST-0001" else 15
            loans.append({
                "customer_id": cid, "loan_id": f"L-{uuid.UUID(int=rng.getrandbits(128)).hex[:10]}",
                "amount": rng.choice([25000, 50000, 100000, 200000]), "income": rng.randint(18000, 150000),
                "employer": rng.choice(EMPLOYERS), "status": "default" if overdue > 30 else "active",
                "disbursed_on": iso(disbursed),
                "repayments": [{"date": iso(disbursed + timedelta(days=30 * k)), "amount": rng.randint(2000, 9000)}
                               for k in range(1, rng.randint(2, 8))],
                "days_overdue": overdue, "collection_calls": 2 if overdue else 0,
            })
            bureau[cid] = {"customer_id": cid, "score": rng.randint(560, 860),
                           "accounts": [{"type": rng.choice(["credit card", "two-wheeler loan", "gold loan"]),
                                         "status": rng.choice(["closed", "current"])}],
                           "pulled_on": iso(disbursed - timedelta(days=3))}

        for k in range(rng.randint(1, 6) if cid != "C-TEST-0001" else 4):
            t = datetime.combine(today - timedelta(days=rng.randint(1, 300)), datetime.min.time(), IST) + timedelta(minutes=rng.randint(0, 1439))
            wallet.append({"customer_id": cid, "txn_id": f"T-{cid}-{k:03d}", "amount": rng.randint(20, 3000),
                           "merchant": rng.choice(MERCHANTS), "txn_time": t.isoformat()})

        lines = []
        for _ in range(rng.randint(3, 10)):
            t = datetime.combine(today - timedelta(days=rng.randint(1, 400)), datetime.min.time(), IST) + timedelta(minutes=rng.randint(0, 1439))
            lines.append({"customer_id": cid, "event_time": t.isoformat(), "event": rng.choice(EVENTS),
                          "device_id": str(uuid.UUID(int=rng.getrandbits(128))),
                          "ip": f"{rng.choice(['203.0.113', '198.51.100'])}.{rng.randint(1, 254)}"})
        events[cid] = sorted(lines, key=lambda e: e["event_time"])

        if cid == "C-TEST-0001" or rng.random() < 0.2:
            tickets.append({"customer_id": cid, "ticket_id": f"S-{cid}-001",
                            "channel": rng.choice(["app", "email", "phone"]),
                            "text": "My repayment was debited twice. Please check.",
                            "created_at": iso(today - timedelta(days=rng.randint(1, 200)))})

    # A known teen account linked to the test customer, for the later children release.
    teen = customer(rng, "C-TEST-0002", teen=True, parent="C-TEST-0001", today=today)
    teen.update(full_name="Test Teen Two", email="test.teen.two@example.com")
    customers.append(teen)
    return {"customers": customers, "loans": loans, "wallet": wallet, "tickets": tickets,
            "bureau": bureau, "events": events}


def write_files(data: dict, out: Path) -> None:
    """Write the dataset as JSON files (used offline and by the tests)."""
    out.mkdir(parents=True, exist_ok=True)
    for name in ("customers", "loans", "wallet", "tickets", "bureau", "events"):
        (out / f"{name}.json").write_text(json.dumps(data[name], indent=1))


def load(data: dict, session) -> None:
    """Write the dataset into the six stores of the account the session signs in to."""
    from decimal import Decimal

    def ddb(item):
        # DynamoDB needs Decimal instead of float for numbers.
        return json.loads(json.dumps(item), parse_float=Decimal)

    reg = register.load()
    account = session.client("sts").get_caller_identity()["Account"]
    names = register.store_names(reg, account)
    dynamo = session.resource("dynamodb")
    for store, rows in (("customers-db", data["customers"]), ("loans-db", data["loans"]),
                        ("wallet-db", data["wallet"]), ("tickets-db", data["tickets"])):
        with dynamo.Table(names[store]).batch_writer() as w:
            for row in rows:
                w.put_item(Item={k: v for k, v in ddb(row).items() if v is not None})
    s3 = session.client("s3")
    for cid, report in data["bureau"].items():
        s3.put_object(Bucket=names["bureau-reports"], Key=f"bureau/{cid}.json", Body=json.dumps(report))
    for cid, lines in data["events"].items():
        s3.put_object(Bucket=names["app-events"], Key=f"events/{cid}.jsonl",
                      Body="\n".join(json.dumps(x) for x in lines))


def main(argv=None) -> int:
    """Command line: generate, write files, and optionally load into AWS."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--customers", type=int, default=200)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="data")
    ap.add_argument("--load", action="store_true", help="load into the AWS account")
    ap.add_argument("--profile")
    args = ap.parse_args(argv)
    data = build(args.customers, args.seed)
    write_files(data, Path(args.out))
    print(f"Wrote {len(data['customers'])} customers, {len(data['loans'])} loans, {len(data['wallet'])} "
          f"wallet transactions, {len(data['tickets'])} tickets to {args.out}/")
    if args.load:
        import boto3
        load(data, boto3.Session(profile_name=args.profile, region_name="ap-south-1"))
        print("Loaded into the account.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
