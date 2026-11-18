# Operating model: who runs DPDP compliance

**DPDP in Practice · Operating model.** Companion release to Release 3 (`v0.4.1`). No AWS code.

Releases 1 to 3 built controls that run in an AWS account. Each one ended with "Beyond the code": the decisions, owners and procedures the code depends on. This release brings those together into one model that a company can adopt: who is accountable, who decides what, and what reaches the board of directors.

It is written for the people who will be asked to adopt it: the board of directors, the CEO, the person who leads privacy, the CISO, the CTO, General Counsel and Internal Audit.

---

## What the law requires, and what it leaves to the company

The Act places responsibility on the company as a Data Fiduciary. It says little about how the company organises itself. This model keeps the two apart, so that nobody mistakes a design choice for a legal duty.

| Required by the law | Provision |
|---|---|
| The company is responsible for compliance, including for processing by its Data Processors | Act s.8(1) |
| Appropriate technical and organisational measures to make sure the Act and the Rules are observed | Act s.8(4); Rule 6(1)(g) for the security safeguards |
| A published contact who can answer questions about processing | Act s.8(9); Rule 9 |
| An effective grievance mechanism, with a published reply period of no more than 90 days | Act s.8(10), s.13; Rule 14(3) |
| Breach intimation to each affected person and to the Data Protection Board, with a detailed report within 72 hours | Act s.8(6); Rule 7 |
| Significant Data Fiduciaries only: a Data Protection Officer based in India and responsible to the board of directors; an independent data auditor; a yearly impact assessment and audit | Act s.10(2); Rule 13 |

| A design choice of this model, recommended but not required |
|---|
| A governance charter adopted by the board of directors |
| A Privacy Lead with a written mandate, for companies that are not Significant Data Fiduciaries |
| A monthly privacy committee |
| Decision rights, each with one decider |
| A RACI with one accountable person for each of the 40 obligations |
| A one-page quarterly report to the board of directors |
| A policy index that maps every obligation to a written rule |
| Impact assessments for high-risk processing, even where not required |

**A Data Protection Officer is required only for a Significant Data Fiduciary** (Section 10(2)(a)). Every other company needs a person whose contact details it publishes (Section 8(9), Rule 9). This model calls that person the Privacy Lead.

---

## The files

| File | What it is |
|---|---|
| [`governance-charter.md`](governance-charter.md) | Scope, accountability, the privacy committee, decision rights, escalation and reporting. The document the board of directors adopts |
| [`privacy-office-and-dpo-mandate.md`](privacy-office-and-dpo-mandate.md) | The Privacy Lead's mandate, and what changes if the company is notified as a Significant Data Fiduciary |
| [`raci.xlsx`](raci.xlsx) | One row for each of the 40 obligations in the Obligations Matrix, with one accountable role per row, checked by a formula |
| [`board-report-template.md`](board-report-template.md) | The one-page quarterly report to the board of directors |
| [`policy-index.md`](policy-index.md) | Which policy or procedure covers which obligation, its owner, and where it is built in this project |
| [`dpia-template.md`](dpia-template.md) | A Data Protection Impact Assessment template, with a worked example: the teen wallet account |

Each file is filled in for Fernleaf Finance (fictional), so it can be read as a finished example and then replaced with your own entries.

---

## How to adopt it, in order

1. **Confirm the scope.** Which entities and business lines process digital personal data, and whether any data leaves India. Use section 2 of the charter.
2. **Name the people.** The CEO is accountable for the programme. Name the Privacy Lead, the CISO, the business owners and the head of Internal Audit.
3. **Agree the RACI.** Go through the 40 rows of `raci.xlsx` with each accountable person. Change the assignments to fit the company, keep one A per row, and have each person agree their rows in writing.
4. **Agree the decision rights.** Section 5 of the charter: one decider for each decision, and who must agree.
5. **Board adoption.** The board of directors adopts the charter and appoints the Privacy Lead. Record it in a board resolution.
6. **Start the cycle.** Hold the first privacy committee, publish the Privacy Lead's contact details (Rule 9), and send the first quarterly report within one quarter.
7. **Check it.** Internal Audit checks, within the first year, that the charter works as written.

---

## How it connects to the rest of this project

| Where | What the operating model adds |
|---|---|
| The Obligations Matrix (Release 0) | Its column "Owner" is filled in by the RACI, row for row, using the same control identifiers |
| The personal data register (Release 1) | The charter says who approves a new store and a new purpose |
| Discovery (Release 2) | Business owners are accountable for the register of their systems; the Privacy Lead for the register as a whole |
| Prevent (Release 3) | Exceptions to a security rule: the system owner decides, the CISO must agree, and every exception expires within 90 days. The Release 3 guide first named both as accountable; it is corrected in this release so that one person decides |
| Later releases | Notice, consent, retention, erasure, breach response, rights and vendors each get their owner from the RACI |

---

## Beyond the documents

**1. The decision management takes.** The board of directors adopts the charter and names the Privacy Lead. Without that resolution, the model is a draft.

**2. Owners.**

| Activity | Board of directors | CEO | Privacy Lead | General Counsel | Internal Audit |
|---|---|---|---|---|---|
| Adopting the charter | A | R | R | C | I |
| Agreeing the RACI | I | A | R | C | I |
| The quarterly report | I | A | R | C | I |
| Independent check that the model works | I | I | I | I | A |

**3. The procedure.** Charter adopted; committee constituted; RACI agreed row by row; contact details published; first quarterly report within one quarter; Internal Audit's check within a year.

**4. The evidence.** The board resolution; the signed RACI; committee minutes; the quarterly reports; Internal Audit's report.

**5. Effort** (indicative, for a mid-sized company). Three to six weeks to agree, most of it in meetings. The documents themselves are the smaller part.

**6. Beyond AWS.** None of this depends on technology. It applies to any company that processes digital personal data.

---

## What this release does not do

- **It is not legal advice.** The mapping of duties to roles is a professional judgement. Have the charter and the RACI reviewed by your own counsel before adoption.
- **It does not cover sector regulators.** A lender also answers to the Reserve Bank of India, and every company reports certain cyber incidents to CERT-In within six hours. Those duties sit alongside this model.
- **Fernleaf Finance is fictional.** Its titles, assignments and figures are a worked example, not a recommendation for any real company's structure.

---

Not legal advice.
