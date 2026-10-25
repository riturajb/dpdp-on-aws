# DPDP on AWS

**A working compliance system for India's Digital Personal Data Protection Act, 2023 and the DPDP Rules, 2025, built on Amazon Web Services and released free.**

Most organisations still meet their DPDP obligations through policies, spreadsheets and manual processes. Those documents describe what should happen. They do not check whether it happened.

This project turns the obligations of the Act and the Rules into controls that run in an AWS account, act automatically, and retain evidence of what they did. Every part is published here with the legal provision it addresses and the steps to run it.

> **Status:** Release 1 (Foundations, and know what you hold) is available. Release 2 is expected in early November 2026. The main DPDP obligations apply from **13 May 2027**.

---

## What the system will do

| Part | What it will do | Main DPDP provisions |
|---|---|---|
| **Find** | Scan databases, storage buckets, logs and backups daily for personal data, including Aadhaar and PAN numbers, and flag any location the register does not list. | Act s.8(5); Rule 6(1)(a) |
| **Prevent** | Check every infrastructure change before release. Block personal data outside approved regions, unencrypted storage, and logs kept for less than one year, and record the reason. | Rule 6(1)(a), Rule 6(1)(e); Act s.16 |
| **Enforce** | Keep consent as a tamper-evident record that systems check before using personal data. When consent is withdrawn, stop marketing, SMS, WhatsApp and call-centre feeds automatically. Exclude children's accounts from tracking, profiling and targeted advertising. | Act s.6(4), s.6(6), s.6(10), s.9 |
| **Erase** | Delete what can be deleted. Seal what a law requires to be kept: restricted, every read logged, each record with its own expiry date. Keep backups for weeks, not years, and re-apply every erasure after any restore. Verify by searching for a deleted test customer. | Act s.8(7), s.12(3); Rule 8(3) |
| **Respond** | Draft customer communications from system records and send them only after human approval. Start the breach clock from a security alert, identify affected customers, and draft the 72-hour report to the Data Protection Board. | Act s.8(6), s.13; Rule 7, Rule 14 |
| **Prove** | Test controls daily. Protect results against alteration, map them to DPDP and ISO/IEC 27001, and make them reproducible by auditors. Give management a single view of open gaps, penalties and deadlines. | Act s.8(1), s.8(5); Rule 6(1)(g) |

An AI assistant will answer questions from the evidence and prepare drafts. It will not make compliance decisions. Every decision remains with a named person.

---

## The model company: Fernleaf Finance

The system is built and tested on **Fernleaf Finance**, a fictional Indian lending and wallet company running on AWS in the Mumbai region (ap-south-1). It has the complexity of a real one:

- Aadhaar and PAN-based customer verification (KYC) through a third-party provider
- Credit bureau checks
- Teen wallet accounts opened with verifiable parental consent
- Outsourced collection calls through a call centre
- SMS, WhatsApp and email communication vendors
- Regulation by the Reserve Bank of India as well as under DPDP, where retention and reporting rules differ

Fernleaf Finance does not exist. Any resemblance to a real company is unintended.

**All customer data in this project is synthetic.** No real personal data is used, stored or published. Sample Aadhaar and PAN numbers are generated so that they cannot belong to a real person; the Aadhaar numbers deliberately fail the Aadhaar check digit.

---

## Available now: Release 1, Foundations, and know what you hold

Release 1 builds the AWS foundation that every later release depends on, and the first DPDP controls on top of it: a register of personal data that checks itself, logs that no administrator can erase, and storage that cannot leave Mumbai.

### What it proves

| DPDP provision | What the system does | Test |
|---|---|---|
| Section 4; Section 7 | Every category of personal data has a recorded purpose and legal basis; a data flow without one is blocked before it is merged | T1, T3 |
| Section 8(1) | The company knows what it holds, where, why and who receives it, and the register matches the stores that exist in the account | T2, T4 |
| Rule 6(1)(b) | Nobody signs in with stored passwords or access keys | T7 |
| Rule 6(1)(c) | The organisation's audit trail cannot be stopped | T5f |
| Rule 6(1)(e) | Logs cannot be deleted, shortened or weakened, even by an administrator, and are kept for one year | T5a to T5e |
| Section 16 | Storage cannot be created outside Mumbai | T6 |

Section 16 does not require personal data to stay in India; it allows the Central Government to restrict transfers to notified countries. Keeping data in Mumbai is a design choice of this build, consistent with the Reserve Bank of India's requirement to store payment system data in India.

### What is included

| Folder | Contents |
|---|---|
| [`register/`](register/) | The personal data register of Fernleaf Finance (fictional): every category of personal data, its stores, purposes, legal basis, vendors, retention and legal reason |
| [`policies/scp/`](policies/scp/) | Four guardrail policies (service control policies), explained statement by statement |
| [`terraform/`](terraform/) | The AWS organisation, its accounts and staged guardrails; the organisation trail; locked log and evidence buckets; account baselines; the model company's data stores; budget alerts |
| [`tools/`](tools/) | The register check, the customer summary, the synthetic data generator and the evidence recorder |
| [`tests/`](tests/) | Fourteen tests. Three run offline on every pull request; eleven run live against AWS |
| [`scripts/`](scripts/) | State bucket set-up and the bootstrap log helper |
| [`docs/`](docs/) | The setup guide, the Release 1 guide and the project standards |
| [`.github/workflows/`](.github/workflows/) | Checks on every pull request: Terraform format, validation and lint; secret and misconfiguration scans; the register check and offline tests |

### How to run it

1. Read **Before you start** in the [Setup Guide](docs/SETUP_GUIDE.md). Use a new AWS account created only for this build: it creates an AWS organisation, and logs and evidence that stay locked after you finish.
2. Build the platform with the [Setup Guide](docs/SETUP_GUIDE.md): the AWS organisation, sign-in, guardrails, logging, evidence storage and cost alerts.
3. Build the release with the [Release 1 Guide](docs/RELEASE_1_GUIDE.md): the model company, the synthetic customers, the register and the tests.

Both guides give numbered steps, the result to expect after each step, and what to do if it differs. They work from a standard AWS account or from an account created with AWS's newer sign-up.

### How it is tested, and where the evidence is kept

Each test attempts something the law requires to be true, or requires to be impossible, and writes an evidence record: the control, the time, what was attempted, the response from AWS, the outcome, the Git commit of the test code, and a SHA-256 checksum. Live evidence is stored in an S3 bucket with Object Lock in compliance mode, where nobody, including the root user, can change or delete it before its retention date. An auditor with read-only access can read a record, confirm its lock and recompute its checksum.

### Cost and removal

The build is designed to stay within a budget of USD 18 a month for the whole organisation (about INR 1,500), with alerts at one third, two thirds and the full amount. A guardrail blocks services with high fixed monthly charges. The model company's stores are removed in the last step of the [Release 1 Guide](docs/RELEASE_1_GUIDE.md). The log and evidence buckets are locked by design: they cannot be emptied early, and they are removed by closing the accounts, which AWS completes after 90 days. The [Setup Guide](docs/SETUP_GUIDE.md), Part 11, gives the steps.

### Limitations

- No notice or consent yet. They arrive in Release 4.
- Changes are applied from a laptop. The approval-gated pipeline arrives in Release 2.
- Guardrails do not apply to the AWS management account; that is how AWS Organizations works. The management account holds no workloads, is protected by multi-factor authentication, and any attempt to stop the trail is recorded.
- IAM Identity Center runs in one region that AWS cannot change later: US East (N. Virginia) for an organisation created through AWS's newer sign-up, or Mumbai when it is enabled as in the Setup Guide, Part 3.0. All personal data stays in Mumbai.
- One person holds every role. In a real organisation, a second person would approve changes.
- The retention periods for KYC, lending and wallet records are placeholders until confirmed against the anti-money-laundering record rules and the Reserve Bank of India's directions.
- Vendors are entries in the register; no data is sent to any real vendor.

---

## Release 0: the blueprint

[`blueprint/DPDP_Obligations_Matrix.xlsx`](blueprint/DPDP_Obligations_Matrix.xlsx) (version 3) is a gap-analysis workbook covering the duties in the Act and the Rules. It has 40 rows, one for each duty, and accounts for every section of the Act, every Rule and every Schedule.

| Sheet | Contents |
|---|---|
| Start Here | How to use the workbook, how the control identifiers are built, and when the Act applies (Section 3) |
| Obligations Matrix | One row per legal duty: plain-English requirement, main provision, the provisions the row covers, related rows, link to the exact text, ISO/IEC 27001:2022 Annex A reference, who it applies to, trigger, time limit, date in force, maximum penalty, actions for the governance team and for engineering, evidence to keep, and columns for your status, owner, gap notes and target date |
| Legal Text | The exact wording of each provision, as published in the Gazette of India, including the Illustrations under Rules 8(3) and 10 |
| Event Playbook | What must happen when a specific event occurs, such as a breach, a withdrawal of consent or an erasure request, and the time allowed |
| Timeline | Commencement dates and days remaining |
| Gap Summary | Counts by status and priority, calculated from the matrix |
| Penalties | Maximum penalties under the Schedule to the Act |
| Coverage | Every provision of the Act and the Rules (83 in all), with the row that covers it or the reason it does not apply to companies |
| Identifier Change Log | Changes to control identifiers and rows between versions |
| Sources | Primary sources and commentary used |

Control identifiers are taken directly from the law, for example `DPDP-Act-S8(7)` or `DPDP-Rule-6(1)(e)`, so any reader can trace a control back to the provision it meets.

See [`blueprint/HOW_TO_USE.md`](blueprint/HOW_TO_USE.md) for guidance on using the workbook for a gap assessment.

---

## Release plan

Each release is published here with release notes and announced on LinkedIn. Timings are indicative and may move as the work progresses; any change is recorded in the release notes and the [changelog](CHANGELOG.md).

| Release | Expected | Content | Status |
|---|---|---|---|
| 0 | October 2026 | Blueprint: the DPDP Obligations Matrix and project standards | **Available** |
| 1 | Late October 2026 | Foundations, and know what you hold: a register of personal data with its purpose and legal basis, logs that no administrator can erase, and a Mumbai-only guardrail | **Available** |
| 2 | Early November 2026 | Find: what the company actually holds, compared with what its register says, including Aadhaar and PAN numbers | Planned |
| 3 | Mid-November 2026 | Prevent: security safeguards enforced before a change is released, and changes outside the process detected | Planned |
| 4 | Mid-November 2026 | Notice and consent: an itemised notice, specific consent, and proof of what each person agreed to | Planned |
| 5 | Late November 2026 | Withdrawal: as easy as consenting, and processing stops, including at vendors | Planned |
| 6 | Early December 2026 | Who gives consent: verifiable parental consent, no tracking of children, and consent through a Consent Manager | Planned |
| 7 | Early December 2026 | Retention and conflicts with other laws: the legal reason and expiry date for every record | Planned |
| 8 | Mid-December 2026 | Erasure: delete, seal what must be kept, keep backups short, and verify | Planned |
| 9 | Late December 2026 | Breach response: the 72-hour clock, affected customers and draft notices | Planned |
| 10 | Late December 2026 | Rights and grievances: requests and grievances tracked against their deadlines | Planned |
| 11 | Early January 2027 | Vendors: which vendor holds which data, and their erasure confirmations | Planned |
| 12 | Mid-January 2027 | Prove: daily control tests, auditor reperformance and a management view | Planned |
| 13 | Late January 2027 | AI assistant with defined limits | Planned |

The complete system is planned to be tested end to end and tagged v1.0.0 well before the main obligations apply on 13 May 2027.

---

## How each release is documented

Every release states:

1. **The obligation**: the DPDP provision it addresses, quoted from the Gazette text.
2. **What was built**: the AWS services used and why.
3. **How to run it**: step-by-step instructions for your own AWS account.
4. **How to test it**: the test, what a pass looks like, and where the evidence is stored.
5. **What it costs**: the expected monthly cost and how to remove what it created.
6. **Limitations**: what the release does not cover.

Project conventions for commit messages, tests and evidence are set out in [`docs/STANDARDS.md`](docs/STANDARDS.md).

---

## Using this in your organisation

This is a reference implementation that any organisation on AWS can adapt. The controls, tests and evidence formats are designed to be reused, not only read.

Your own implementation will depend on your sector, your other regulators, your systems and your vendors. If your team needs help adapting it, I will be glad to guide them. Contact details are below.

---

## Important notes

- **This is not legal advice.** The mapping of controls to legal provisions reflects the author's professional interpretation. Your organisation should obtain its own legal opinion on how the Act and Rules apply to it.
- **Legal text** is reproduced from the Digital Personal Data Protection Act, 2023 and the Digital Personal Data Protection Rules, 2025 as published in the Gazette of India.
- **ISO/IEC 27001 references** give the control number with a description in the author's own words. The standard's text is not reproduced. Obtain the standard from ISO or the Bureau of Indian Standards.
- **No real personal data** is used anywhere in this project.
- **AWS** is a trademark of Amazon.com, Inc. or its affiliates. This project is not affiliated with or endorsed by Amazon Web Services.
- To report a security concern, see [`SECURITY.md`](SECURITY.md).

---

## Licence

Released under the [Apache License 2.0](LICENSE). You may use, adapt and redistribute the code and documents, including commercially, subject to the terms of the licence.

---

## Author

**Rituraj**
Principal Cybersecurity Consultant · Founder, Defenaar Consulting
CISA · CCSK · ISO/IEC 27001, 27701 and 22301 Lead Auditor · 22+ years in cybersecurity, governance, risk and compliance

LinkedIn: [linkedin.com/in/ritu-b](https://www.linkedin.com/in/ritu-b/)
