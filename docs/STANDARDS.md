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

Every change is recorded in this format:

```
<Short title of the change>

Control:     <control identifier, or "None">
Change:      <what was changed, in one or two sentences>
Reason:      <why it was changed>
Tested by:   <name of the test, or "Not applicable">
Approved by: <name>
```

Example:

```
Block log groups kept for less than one year

Control:     DPDP-Rule-6(1)(e)
Change:      Added a pre-release check that rejects any CloudWatch log group
             with a retention period shorter than 365 days.
Reason:      Rule 6(1)(e) requires logs to be retained for at least one year.
Tested by:   tests/prevent/test_log_retention.py
Approved by: Rituraj
```

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

Every test result will include:

- the control identifier
- the date and time of the test (IST)
- a one-sentence summary, for example: *"On 13 October 2026 at 10:30 IST, all 14 log groups were checked; all were retained for 365 days or more. Result: Pass."*
- the version of the script that produced it (the Git commit reference)
- a SHA-256 checksum of the result file

Results will be stored in a storage location that prevents alteration or deletion for a fixed period. An auditor will be able to rerun any test and compare the outcome with the stored result.

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
