# Project standards

These standards apply to everything published in this repository. They exist so that an auditor, a Data Protection Officer or an engineer can read any change, test or result without needing the author to explain it.

---

## 1. Language

- Plain, formal English.
- No abbreviations without their full form on first use in each document.
- Dates written in full, with the time zone: **13 October 2026, 10:30 IST**.
- Legal provisions written in full on first use: *Digital Personal Data Protection Act, 2023, Section 8(6)*. The short form `Act s.8(6)` may be used afterwards.

---

## 2. Control identifiers

Every control carries the identifier of the legal provision it meets:

| Format | Example | Meaning |
|---|---|---|
| `DPDP-Act-S<section>(<sub-section>)` | `DPDP-Act-S8(7)` | Act, Section 8(7) |
| `DPDP-Rule-<rule>(<sub-rule>)` | `DPDP-Rule-6(1)(e)` | Rules, Rule 6(1)(e) |

Where a control meets more than one provision, the main provision is listed first.

---

## 3. Commit messages

Every change is recorded in this format: a short title, a blank line, one or two sentences on what changed and why, a blank line, then the trailers. Git and GitHub read the trailers as structured data, so commits can be listed by control.

```
<Short title of the change>

<What was changed and why, in one or two sentences.>

Control: <control identifier, several separated by commas, or "None">
Release: <release number>
Tested-by: <test file, or "Not applicable">
Approved-by: <name>
```

Example:

```
Foundations: Keep logs for one year in a locked bucket

The organisation trail writes to a bucket with Object Lock in governance
mode and a default retention of 365 days. Evidence buckets use
compliance mode for live results and governance mode for the sandbox.

Control: DPDP-Rule-6(1)(e)
Release: 1
Tested-by: tests/foundations/test_t5_logs_cannot_be_erased.py
Approved-by: Rituraj
```

Every commit is signed, and every change reaches `main` through a pull request with a merge commit.

---

## 4. Tests

Each test file begins with a header in this format:

```
Control:          <control identifier>
What is checked:  <one sentence>
Pass means:       <one sentence>
Fail means:       <one sentence>
Evidence stored:  <location of the result>
```

---

## 5. Results and evidence

Every test writes one evidence record with:

- the control identifier and the name of the test
- the date and time of the test (IST)
- what was attempted, and the response received from AWS
- the outcome: pass or fail
- the version of the code that ran the test (the Git commit reference)
- a SHA-256 checksum of the record

Live results are stored in an S3 bucket with Object Lock in compliance mode, which prevents alteration or deletion until the retention date. An auditor can read a record with read-only access, confirm its lock, recompute its checksum, and rerun the test to compare the outcome with the stored result.

---

## 6. Data

- **Synthetic data only.** No real personal data is ever used, stored or published.
- Sample Aadhaar and PAN numbers are generated so that they cannot belong to a real person.
- Names, addresses and phone numbers in sample data are invented.

---

## 7. Secrets and account details

The following are never committed to this repository:

- AWS access keys, secret keys or session tokens
- AWS account numbers
- Passwords, API keys or tokens of any kind
- Terraform state files or variable files containing real values
- Email addresses or phone numbers of real people

Before every publication:

1. GitHub secret scanning and push protection remain enabled on this repository.
2. The files are checked locally with a secret-detection tool (`gitleaks`).
3. Example configuration files use placeholder values such as `123456789012` for an account number.
