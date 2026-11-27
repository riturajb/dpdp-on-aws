# Governance charter for personal data protection

A template, filled in for Fernleaf Finance (fictional). Replace the Fernleaf entries with your own and have the board adopt the result.

The Act requires the outcomes; it does not prescribe this structure. Where a row cites a provision, the provision is the duty the row serves. The structure itself (a charter, a committee, decision rights, escalation and reporting) is a recommended design.

---

## 1. Purpose

This charter sets out who is accountable for the company's compliance with the Digital Personal Data Protection Act, 2023 and the Digital Personal Data Protection Rules, 2025, who decides what, and what is reported to the board of directors.

**Legal basis for having it.** The Act makes the company responsible for compliance, including for processing done on its behalf by Data Processors (Section 8(1)). It requires appropriate technical and organisational measures to make sure the Act and the Rules are observed (Section 8(4)) and that the security safeguards work in practice (Rule 6(1)(g)). The Act does not prescribe a charter, a committee or a board report. This charter is the organisational measure the company chooses.

**Two Boards.** In this charter, "the board" means the company's board of directors. "The Data Protection Board" means the regulator set up under Section 18 of the Act.

**Fernleaf Finance.** Adopted by the board of directors on [date of the board resolution]. Reviewed every year, and whenever the company is notified as a Significant Data Fiduciary.

---

## 2. Scope

| Item | What to state | Fernleaf Finance |
|---|---|---|
| Entities | Every company in the group that processes digital personal data | Fernleaf Finance only |
| Business lines | Each line that processes personal data | Lending, wallet (including teen wallet accounts), collections, marketing, customer service |
| People whose data is processed | Customers, prospects, employees, others | Customers and prospects, parents of teen wallet holders, employees, vendor contacts |
| Where processing happens | India, and any country data is transferred to (Section 16) | India (AWS Mumbai region); no transfers outside India |
| Other laws that apply alongside | Sector rules that also govern the same data (Section 38) | Reserve Bank of India directions for lenders and wallets; CERT-In directions on incident reporting; tax and anti-money-laundering record-keeping |
| Significant Data Fiduciary | Whether the company has been notified under Section 10(1) | Not notified. The charter is written so that the change is small if it is |

---

## 3. Accountability

| Role | Accountable for | Fernleaf Finance |
|---|---|---|
| Board of directors | Adopting this charter; appointing the Privacy Lead (or the Data Protection Officer, if notified as a Significant Data Fiduciary); receiving the quarterly report and deciding what is escalated to it | Board of directors; the Audit Committee reviews the quarterly report first |
| Chief executive (CEO or MD) | The compliance programme as a whole (Section 8(1)); approving intimations of a personal data breach; deciding escalations | Chief Executive Officer |
| Privacy Lead | Running the programme day to day; the personal data register; notices, consent, rights and grievances; preparing breach intimations; chairing the privacy committee. Also the person whose contact details are published under Section 8(9) and Rule 9 | Head of Privacy |
| Chief Information Security Officer (CISO) | Security safeguards (Section 8(5), Rule 6(1)) and their effectiveness (Rule 6(1)(g)) | Chief Information Security Officer |
| Chief Risk Officer | Model risk: the risk tier of each AI system and model, independent validation before deployment and after change, and approval to deploy or restart (RBI draft guidance on model risk management, 24 June 2026, not final). Added with the AI governance release (`ai-governance/`) | Chief Risk Officer |
| Business owners | The processing in their business line: its purpose, its legal basis, and the accuracy of the register for their systems | Heads of Lending, Wallet, Collections, Marketing and Customer Service; the Head of HR for employee data |
| Head of Internal Audit | An independent check, at least once a year, that this charter works as written | Head of Internal Audit, reporting to the Audit Committee |

**If the company is notified as a Significant Data Fiduciary,** the Privacy Lead's role becomes that of a Data Protection Officer, who must represent the company under the Act, be based in India, be an individual responsible to the board of directors, and be the point of contact for the grievance redressal mechanism (Section 10(2)(a)). The company must also appoint an independent data auditor (Section 10(2)(b)). See `privacy-office-and-dpo-mandate.md`.

---

## 4. Privacy committee

Recommended design; not required by the Act.

| Item | Fernleaf Finance |
|---|---|
| Chair | Privacy Lead |
| Members | CISO, Chief Technology Officer, Chief Risk Officer, General Counsel and Company Secretary, the five business owners, Head of HR, Head of Procurement |
| Attends, without a vote | Head of Internal Audit |
| Meets | Monthly, and within one working day of a personal data breach |
| Quorum | The chair, the CISO, the General Counsel, and the business owner of every item on the agenda |
| Records | Minutes with each decision, its owner and its date, kept as evidence for three years |
| Standing agenda | Open gaps against the Obligations Matrix; changes to the register; changes to the AI register and its open decisions; exceptions granted and expiring; changes outside the process flagged by detection (Release 3); rights requests and grievances against their time limits; vendors added or changed; incidents |

---

## 5. Decision rights

Each decision has one decider: a named role, or the privacy committee. "Must agree" means the decision cannot be taken without that role's written agreement. Every decision is recorded where the last column says.

| Decision | Decides | Must agree | Consulted | Recorded in | Provision |
|---|---|---|---|---|---|
| A new purpose of processing, and its legal basis (consent, or a named clause of Section 7) | Privacy committee | General Counsel | Business owner | Personal data register; committee minutes | Act s.4, s.6, s.7 |
| A new store or system that will hold personal data | Business owner | Privacy Lead | CISO, CTO | Personal data register | Act s.8(1); Rule 6(1) |
| A new Data Processor, or new personal data shared with an existing one | Business owner | Privacy Lead and CISO | Head of Procurement, General Counsel | Vendor register; signed contract with security and erasure clauses | Act s.8(2), s.8(7)(b); Rule 6(1)(f) |
| Notice text and each language version | Privacy Lead | General Counsel | Business owner | Versioned notice library | Act s.5; Rule 3 |
| Using a Consent Manager, and which one | Privacy committee | General Counsel | CTO | Committee minutes; check of registration with the Data Protection Board | Act s.6(7) to s.6(9); Rule 4 |
| Transfer of personal data to a new country | Privacy Lead | General Counsel | CISO, business owner | Register of transfers | Act s.16 |
| Keeping data after its purpose has ended because another law requires it, or refusing an erasure request for that reason | General Counsel (whether the other law requires it) | Privacy Lead | Business owner | Register of conflicts with other laws; reply to the person | Act s.8(7), s.12(3), s.38; Rule 8(3) |
| An exception to a security rule (for example, a plan-check rule from Release 3) | System owner (the business owner of the system) | CISO | Privacy Lead | Exceptions register, with a reason and an expiry date of no more than 90 days | Rule 6(1); Rule 6(1)(g) |
| Approving the intimations of a personal data breach to the Data Protection Board and to affected persons | CEO | (none: speed matters) | Privacy Lead, CISO, General Counsel | Breach file, with the time of every step | Act s.8(6); Rule 7 |
| Asking the Data Protection Board for more time for the 72-hour report | CEO | General Counsel | Privacy Lead | Breach file | Rule 7(2)(b) |
| Replying to a request for information from the Government | General Counsel | (none) | Privacy Lead, CTO | Register of Government requests | Act s.36; Rule 23 |
| A voluntary undertaking to the Data Protection Board, or an appeal against its order | CEO | Board of directors | General Counsel, Privacy Lead | Board minutes | Act s.29, s.32 |
| Relying on an exemption under Section 17 | General Counsel | Privacy Lead | Business owner | Register of exemptions relied on | Act s.17 |
| A new AI system, or a new use of an existing one | Business owner | Privacy Lead, CISO and Chief Risk Officer | CTO, General Counsel | AI register; impact assessment; committee minutes | Act s.4, s.8(1), s.8(5) |
| What an AI system may do: its tools, and which actions a person approves | Business owner | Chief Risk Officer and Privacy Lead | CISO, CTO | AI register | Act s.8(1), s.8(5) |
| The risk tier of an AI system or model, and deploying it after validation | Chief Risk Officer | (none) | Business owner, CTO | AI register; validation report | RBI draft guidance on model risk management |
| Suspending an AI system (read-only or halt) | CISO; the business owner may also trigger it | (none: speed matters) | Chief Risk Officer, Privacy Lead | AI register; incident file | Act s.8(5); Rule 6(1)(d) |
| Restarting a suspended AI system | Chief Risk Officer | CISO | Business owner | AI register; incident file | RBI draft guidance on model risk management |
| An AI tool approved for staff use with personal data | CTO | CISO and Privacy Lead | Head of Procurement | AI register | Act s.8(2), s.8(5); Rule 6(1)(f) |

**Breach approval when the CEO cannot be reached.** Every personal data breach must be intimated to affected persons and to the Data Protection Board without delay, and the detailed report is due within 72 hours (Rule 7). The Act and the Rules set no threshold of seriousness below which a breach need not be reported. If the CEO cannot be reached within two hours of the request for approval, the Privacy Lead approves, and the CEO is told as soon as possible.

---

## 6. Escalation

| To | When | Within |
|---|---|---|
| CEO | Any personal data breach; any exception requested beyond 90 days; any gap in a Priority 1 row of the Obligations Matrix that will miss its target date; any order or inquiry of the Data Protection Board | One working day; for a breach, immediately |
| Board of directors | Any personal data breach that has been intimated to the Data Protection Board; any inquiry or order of the Data Protection Board; any decision to accept a risk that the CEO does not want to accept alone | Within 24 hours for a breach; otherwise at the next meeting, or earlier if the CEO decides |

---

## 7. Reporting to the board

| Report | When | Content |
|---|---|---|
| Quarterly report | Every quarter, to the Audit Committee and then the board | One page, in the form of `board-report-template.md` |
| Breach notice | Within 24 hours of any intimation to the Data Protection Board | What happened, who is affected, what was intimated and when, the next deadline |
| Annual review | Once a year | Internal Audit's check of this charter; changes proposed |

---

## 8. Review

The Privacy Lead reviews this charter every year and whenever the law, the company's business, or its notification status changes. Changes are approved by the board of directors.

---

Not legal advice. The Fernleaf Finance entries are a worked example for a fictional company.
