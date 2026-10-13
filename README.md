# DPDP on AWS

**A working compliance system for India's Digital Personal Data Protection Act, 2023 and the DPDP Rules, 2025, built on Amazon Web Services and released free.**

Most organisations still meet their DPDP obligations through policies, spreadsheets and manual processes. Those documents describe what should happen. They do not check whether it happened.

This project turns the obligations of the Act and the Rules into controls that run every day in an AWS account, act automatically, and retain evidence of what they did. Every part is published here with the legal provision it addresses and the steps to run it.

> **Status:** Release 0 (the blueprint) is available now. The working parts will be released in stages, starting this week, in the run-up to the main DPDP obligations applying on **13 May 2027**.

---

## What the system will do

| Part | What it will do | Main DPDP provisions |
|---|---|---|
| **Find** | Scan every database, storage bucket, log and backup daily for personal data, including Aadhaar and PAN numbers, and flag any new location. | Act s.8(4), s.8(5); Rule 6 |
| **Prevent** | Check every infrastructure change before release. Block personal data outside approved regions, unencrypted storage, and logs kept for less than one year, and record the reason. | Rule 6(1)(a), Rule 6(1)(e); Act s.16 |
| **Enforce** | Keep consent as a tamper-evident record that systems check before using personal data. When consent is withdrawn, stop marketing, SMS, WhatsApp and call-centre feeds automatically. Exclude children's accounts from tracking, profiling and targeted advertising. | Act s.6(4), s.6(6), s.6(10), s.9 |
| **Erase** | Give every record its legal basis for retention and its deletion date. Run erasure across databases, backups, logs and vendors, and verify it by searching for a deleted test customer. | Act s.8(7), s.12(3); Rule 8(3) |
| **Respond** | Draft customer communications from system records and send them only after human approval. Start the breach clock from a security alert, identify affected customers, and draft the 72-hour report to the Data Protection Board. | Act s.8(6), s.13; Rule 7, Rule 14 |
| **Prove** | Test controls daily. Protect results against alteration, map them to DPDP and ISO/IEC 27001, and make them reproducible by auditors. Give management a single view of open gaps, penalties and deadlines. | Act s.8(1), s.8(4), s.6(10) |

An AI assistant will answer questions from the evidence and prepare drafts. It will not make compliance decisions. Every decision remains with a named person.

---

## The model company

The system is built and tested on a **model Indian lending and wallet company** running on AWS in the Mumbai region (ap-south-1). It has the complexity of a real one:

- Aadhaar and PAN-based customer verification (KYC) through a third-party provider
- Credit bureau checks
- Teen wallet accounts opened with verifiable parental consent
- Outsourced collection calls through a call centre
- SMS, WhatsApp and email communication vendors
- Regulation by the Reserve Bank of India as well as under DPDP, where retention and reporting rules differ

**All customer data in this project is synthetic.** No real personal data is used, stored or published. Sample Aadhaar and PAN numbers are generated so that they cannot belong to a real person.

---

## Available now: Release 0, the blueprint

[`blueprint/DPDP_Obligations_Matrix.xlsx`](blueprint/DPDP_Obligations_Matrix.xlsx) is a gap-analysis workbook covering the duties in the Act and the Rules. It contains:

| Sheet | Contents |
|---|---|
| Start Here | How to use the workbook |
| Obligations Matrix | One row per legal duty: plain-English requirement, legal provision, link to the exact text, ISO/IEC 27001:2022 Annex A reference, who it applies to, when it comes into force, status and priority |
| Legal Text | The exact wording of each provision, as published in the Gazette of India |
| Event Playbook | What must happen when a specific event occurs, such as a breach, a withdrawal of consent or an erasure request, and the time allowed |
| Timeline | Commencement dates and days remaining |
| Gap Summary | Counts by status and priority, calculated from the matrix |
| Penalties | Maximum penalties under the Schedule to the Act |
| Identifier Change Log | Changes to control identifiers between versions |
| Sources | Primary sources used |

Control identifiers are taken directly from the law, for example `DPDP-Act-S8(6)` or `DPDP-Rule-7(2)`, so any reader can trace a control back to the provision it meets.

See [`blueprint/HOW_TO_USE.md`](blueprint/HOW_TO_USE.md) for guidance on using the workbook for a gap assessment.

---

## Release plan

Each release will be published here with release notes and announced on LinkedIn.

| Release | Content | Status |
|---|---|---|
| 0 | Blueprint: DPDP obligations matrix and project standards | **Available** |
| 1 | Foundations: AWS account set-up, cost controls, evidence store, model company and synthetic data | Planned |
| 2 | Find: daily discovery of personal data | Planned |
| 3 | Prevent: checks on infrastructure changes before release | Planned |
| 4 | Enforce: consent record, withdrawal and children's accounts | Planned |
| 5 | Erase: retention register, erasure and verification | Planned |
| 6 | Respond: customer communications and breach workflow | Planned |
| 7 | Vendors: tracking which vendor holds which data, and their erasure confirmations | Planned |
| 8 | Prove: daily control tests, auditor evidence and management view | Planned |
| 9 | AI assistant with defined limits | Planned |

The order may change as the work progresses. Any change will be recorded in the release notes.

---

## How each release is documented

Every release will state:

1. **The obligation**: the DPDP provision it addresses, quoted from the Gazette text.
2. **What was built**: the AWS services used and why.
3. **How to run it**: step-by-step instructions for your own AWS account.
4. **How to test it**: the test, what a pass looks like, and where the evidence is stored.
5. **What it costs**: the expected monthly cost and how to remove everything afterwards.
6. **Limitations**: what the release does not cover.

Project conventions for commit messages, tests and evidence are set out in [`docs/STANDARDS.md`](docs/STANDARDS.md).

---

## Cost

The project is designed to run in a personal AWS account at low cost. Services with high fixed monthly charges are avoided or used only for short, stated periods. Each release will include budget alerts and a script to remove what it created.

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

LinkedIn: https://www.linkedin.com/in/ritu-b/
https://defenaar.com

