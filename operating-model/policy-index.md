# Policy index

Which policy or procedure covers which obligation, who owns it, and where it is built in this project. Filled in for Fernleaf Finance (fictional).

The Act and the Rules do not require any particular set of policies. They require the duties to be met, and the company to be able to show it. This index is how the company shows that every duty in the Obligations Matrix has a written rule, an owner and a review date. Every one of the 40 control identifiers appears in at least one row.

Status for Fernleaf Finance: **In place** (approved and in use), **Drafted** (written, not yet approved), **Planned** (not yet written).

| # | Policy or procedure | Covers (control identifiers) | Owner | Reviewed | Built in this project | Fernleaf status |
|---|---|---|---|---|---|---|
| 1 | Data protection policy: the company's commitments and this operating model | DPDP-Act-S8(1), DPDP-Rule-6(1)(g) | Privacy Lead | Yearly | Operating model | Drafted |
| 2 | Personal data register, legal basis and data quality procedure | DPDP-Act-S4, DPDP-Act-S7, DPDP-Act-S8(3) | Privacy Lead | Quarterly | Release 1 (register), Release 2 (discovery) | In place |
| 3 | Data discovery procedure: finding personal data the register does not list | DPDP-Act-S8(1), DPDP-Rule-6(1)(a) | CISO | Quarterly | Release 2 | In place |
| 4 | Notice and consent procedure, including withdrawal and proof of consent | DPDP-Act-S5(1), DPDP-Act-S5(2), DPDP-Act-S6(1), DPDP-Act-S6(4), DPDP-Act-S6(10) | Privacy Lead | Yearly | Releases 4 and 5 | Planned |
| 5 | Consent Manager decision record | DPDP-Rule-4(1) | Privacy Lead | When a Consent Manager is considered | Release 6 | Planned |
| 6 | Children and lawful guardians procedure | DPDP-Act-S9(1), DPDP-Act-S9(3), DPDP-Rule-11(1) | Privacy Lead | Yearly | Release 6 | Planned |
| 7 | Retention schedule and erasure procedure | DPDP-Act-S8(7), DPDP-Rule-8(1), DPDP-Rule-8(3), DPDP-Rule-6(1)(e) | Privacy Lead | Yearly | Releases 7 and 8 | Planned |
| 8 | Register of conflicts with other laws | DPDP-Act-S38, DPDP-Act-S44(2) | General Counsel | Quarterly | Release 7 | Drafted |
| 9 | Information security policy and standards: encryption and masking, access control, logging and monitoring, backups | DPDP-Act-S8(5), DPDP-Rule-6(1)(a), DPDP-Rule-6(1)(b), DPDP-Rule-6(1)(c), DPDP-Rule-6(1)(d), DPDP-Rule-6(1)(e) | CISO | Yearly | Release 1 (guardrails, locked logs), Release 3 (rules, recoverable stores) | In place |
| 10 | Change management and exceptions procedure | DPDP-Rule-6(1)(g), DPDP-Act-S8(5) | CISO | Yearly | Release 3 | In place |
| 11 | Personal data breach response procedure | DPDP-Rule-7(1), DPDP-Rule-7(2), DPDP-Act-S32 | Privacy Lead | Yearly, and after every breach or exercise | Release 9 | Drafted |
| 12 | Rights requests procedure: access, correction, erasure, nomination | DPDP-Act-S11(1), DPDP-Act-S12, DPDP-Act-S14(1), DPDP-Rule-9 | Privacy Lead | Yearly | Release 10 | Planned |
| 13 | Grievance redressal procedure, with the published reply period | DPDP-Act-S13, DPDP-Rule-9 | Privacy Lead | Yearly | Release 10 | Drafted |
| 14 | Data Processor (vendor) management procedure and standard clauses | DPDP-Act-S8(1), DPDP-Rule-6(1)(f), DPDP-Act-S6(4), DPDP-Act-S8(7) | Head of Procurement | Yearly | Release 11 | Drafted |
| 15 | Transfers outside India procedure | DPDP-Act-S16 | Privacy Lead | Yearly | Release 1 (Mumbai-only guardrail) | In place |
| 16 | Requests from the Government and the Data Protection Board | DPDP-Rule-23, DPDP-Act-S32 | General Counsel | Yearly | Release 9 | Planned |
| 17 | Register of exemptions relied on | DPDP-Act-S17(1), DPDP-Act-S17(2)(b) | General Counsel | Yearly | Operating model | Drafted |
| 18 | Significant Data Fiduciary readiness: Data Protection Officer, independent data auditor, yearly assessment and audit | DPDP-Act-S10(2), DPDP-Rule-13 | Privacy Lead | On notification | Operating model (`dpia-template.md`) | Drafted |
| 19 | Policy on the use of AI: AI systems the company builds or runs, AI tools staff use, AI features switched on by vendors (`ai-governance/ai-use-policy.md`) | DPDP-Act-S4, DPDP-Act-S8(1), DPDP-Act-S8(5), DPDP-Rule-6(1)(a), DPDP-Rule-6(1)(f) | CTO | Yearly, and for each new AI system or staff AI tool | AI governance (AI register and check); Releases 12 and 13 | Drafted |

## How to use it

1. Keep the identifiers exactly as in the Obligations Matrix, so a policy can be traced to the law and to the tests that check it.
2. When the matrix changes, check that every identifier still appears in this index.
3. Check each policy's owner against the accountable role for its rows in `raci.xlsx`. They can differ, because one policy can serve rows with different owners, but each difference should be deliberate.
4. A policy marked **In place** must have an approval date and a next review date in the company's own document register.

---

Not legal advice. The Fernleaf Finance entries are a worked example for a fictional company.
