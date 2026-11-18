# Data Protection Impact Assessment: template

A template for assessing new processing, followed by a worked example for Fernleaf Finance (fictional): the teen wallet account.

## When it is required

| Company | Requirement | Provision |
|---|---|---|
| Significant Data Fiduciary | A periodic Data Protection Impact Assessment: a description of the rights of Data Principals and the purpose of processing, an assessment and management of the risk to their rights, and other matters that may be prescribed | Act s.10(2)(c)(i) |
| Significant Data Fiduciary | An assessment and an audit once in every twelve months from notification, with a report of significant observations to the Data Protection Board | Rule 13(1), 13(2) |
| Every other Data Fiduciary | Not required by the Act. Recommended before any new processing that involves children, large volumes, new technology, decisions about people, or a new Data Processor | Recommended practice |

Section 10(2)(c)(i) names three elements: the rights of Data Principals and the purpose of processing; the risk to their rights; and how that risk is managed. Sections 2 to 6 below cover them; the other sections are recommended.

---

## Template

| # | Section | What to write |
|---|---|---|
| 1 | The processing | What is being done, by which business line, using which systems and vendors. Owner and Privacy Lead named |
| 2 | Purpose | Each purpose, specific enough that a person would understand it. Register entry for each |
| 3 | Legal basis | Consent, or the named clause of Section 7, for each purpose |
| 4 | Personal data | Each category of data, whose data it is (including children), where it is stored, who receives it, and whether it leaves India |
| 5 | Rights of Data Principals | How each right works for this processing: notice, withdrawal, access, correction and erasure, grievance, nomination (Act s.5, s.6, s.11 to s.14) |
| 6 | Risks to the rights of Data Principals, and how each is managed | For each risk: what could go wrong for the person, how likely, how severe, the measure taken, and the risk that remains |
| 7 | Necessity | Why each category of data is needed; what was considered and not collected |
| 8 | Retention | How long each category is kept, and the legal reason for any period beyond the purpose (Act s.8(7); Rule 8(3)) |
| 9 | Security safeguards | The safeguards under Rule 6(1)(a) to (g) for this processing |
| 10 | Algorithmic software | For a Significant Data Fiduciary: due diligence that the software used is not likely to pose a risk to the rights of Data Principals (Rule 13(3)) |
| 11 | Decision | Proceed, proceed with conditions, or do not proceed. Signed by the business owner and the Privacy Lead; the CISO signs section 9 |
| 12 | Review | When the assessment will be reviewed, and what change would trigger an earlier review |

---

## Worked example: teen wallet account (Fernleaf Finance, fictional)

**1. The processing.** Wallet accounts for customers aged 13 to 17, opened by a parent from the parent's own Fernleaf account. Business owner: Head of Wallet. Systems: the customer and wallet tables; the KYC provider; the SMS and WhatsApp provider. Privacy Lead: Head of Privacy.

**2. Purpose.**
- Opening and running the teen's wallet: balance, top-ups by the parent, payments.
- Showing the parent the teen's transactions.
- Meeting record-keeping duties for wallet transactions.

**3. Legal basis.** Verifiable consent of the parent, under Section 9(1), for opening and running the account and for showing transactions to the parent. Records that a law requires the company to keep are not a separate purpose: they are retained under the exception in Section 8(7) ("unless retention is necessary for compliance with any law"), and an erasure request is answered under Section 12(3).

**4. Personal data.** The teen's name, date of birth, mobile number and transactions; the parent's identity and the link between the two accounts. Stored in Mumbai (ap-south-1). Shared with the KYC provider (parent only) and the SMS and WhatsApp provider (transaction alerts). Nothing leaves India.

**5. Rights of Data Principals.** The parent exercises the teen's rights on her behalf. The notice to the parent lists the data, the purposes and how to withdraw. Withdrawal closes the wallet once the balance is returned to the parent. Access, correction, erasure and grievance follow the company's procedures, with replies within the published period.

**6. Risks to the rights of Data Principals, and how each is managed.**

| Risk to the person | Likelihood | Severity | Measure | Remaining risk |
|---|---|---|---|---|
| An adult who is not the parent opens an account for a child | Medium | High | Parent verified as an identifiable adult from Fernleaf's own KYC records before the teen account opens (Rule 10(1)(a); the Illustration to Rule 10, Case 3) | Low |
| The teen's transactions are used to profile her or target advertising | Medium | High | Teen accounts excluded from marketing, tracking and behavioural monitoring by a flag checked by every marketing system (Section 9(3)) | Low |
| A teen's data is kept after the account is closed without a reason | Medium | Medium | Expiry date set on every record when the account closes; records a law requires are kept, restricted, and erased when that period ends | Low |
| Transaction alerts reveal a teen's spending to someone other than the parent | Low | Medium | Alerts sent only to the teen's and the parent's verified numbers | Low |
| A breach exposes children's data | Low | High | Encryption, access control and detection as for all personal stores (Releases 1 to 3); breach procedure | Medium; accepted by the CEO |

**7. Necessity.** School name and address were considered and not collected: they are not needed to run a wallet.

**8. Retention.** Account data: erased when the account closes. Transaction records: kept for the period the applicable record-keeping rules require, then erased. Logs: one year (Rule 6(1)(e), Rule 8(3)).

**9. Security safeguards.** As for every personal data store: tagged, registered, not public, recoverable, logs kept for a year (Release 3); found if stored elsewhere (Release 2); stores and logs in Mumbai only (Release 1).

**10. Algorithmic software.** Not applicable: Fernleaf Finance is not a Significant Data Fiduciary, and no automated decisions are made about teens.

**11. Decision.** Proceed with conditions: the marketing exclusion flag and the parent verification must pass their tests before launch. Signed: Head of Wallet, Head of Privacy; section 9: CISO.

**12. Review.** In twelve months, or earlier if the age range, a vendor or the marketing approach changes.

---

Not legal advice. The worked example is for a fictional company; the legal bases shown are its own recorded decisions.
