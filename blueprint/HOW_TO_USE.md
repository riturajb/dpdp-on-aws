# How to use the DPDP Obligations Matrix

The workbook `DPDP_Obligations_Matrix.xlsx` (version 3) is designed for a first gap assessment against the Digital Personal Data Protection Act, 2023 and the Digital Personal Data Protection Rules, 2025.

## Steps

1. **Open the `Start Here` sheet** and read it, including *When the Act applies (Section 3)*. Confirm that the Act applies to your organisation before going further.
2. **Go to `Obligations Matrix`.** Each of the 40 rows is one legal duty.
   - *Provisions covered in this row* names every section, sub-section, Rule and Schedule the row covers.
   - *Other related provisions* points to other rows you should read with it.
3. **Filter on `Applies to`.** Rows for Significant Data Fiduciaries, Consent Managers or other categories may not apply to your organisation. Mark these as *Not applicable to this organisation*.
4. **Fill in the yellow columns** for each remaining row:
   - **Current status**: Not assessed, Not started, Partially in place, In place, or Not applicable to this organisation
   - **Owner**: the full name and designation of the person accountable for the duty
   - **Gap notes**: gaps, decisions or dependencies
   - **Target date**: when the gap will be closed

   The column *Evidence to keep* tells you what proof to collect for each duty.
5. **Read the exact legal text** for any row by selecting *Read the exact text*. It opens the matching row in the `Legal Text` sheet, which reproduces the Gazette wording, including the Illustrations under Rules 8(3) and 10.
6. **Check `Coverage`.** It lists all 83 provisions of the Act and the Rules: 35 have their own row, 28 are grouped into a row, 19 do not apply to companies, and 1 (Section 3) is explained in Start Here.
7. **Review `Gap Summary`.** Counts by status and priority update automatically.
8. **Use `Event Playbook`** to check that your organisation has a defined response, an owner and a time limit for each event, such as a breach or an erasure request.
9. **Use `Timeline`** to plan work against the commencement dates, and **`Penalties`** to see the maximum penalty for each kind of breach.

## When a provision has its own row

A provision has its own row only if a company could meet it while failing the provisions next to it, and it needs a different owner or different evidence. Otherwise it is grouped into the row it belongs with. For example, Rule 6(1) has seven rows, one for each safeguard, because each usually has its own owner and evidence.

## Priority

Each row has a risk weight from 1 to 3, explained on the `Start Here` sheet. Priority follows the weight:

| Risk weight | Priority |
|---|---|
| 3 | Priority 1 |
| 2 | Priority 2 |
| 1 | Priority 3 |

A row shows *Closed* once its status is *In place* or *Not applicable to this organisation*. Address Priority 1 first.

## Control identifiers

Identifiers follow the law itself, for example:

| Identifier | Meaning |
|---|---|
| `DPDP-Act-S8(7)` | Digital Personal Data Protection Act, 2023, Section 8(7) |
| `DPDP-Rule-6(1)(e)` | Digital Personal Data Protection Rules, 2025, Rule 6(1)(e) |

The same identifiers will be used in the code, the tests and the evidence in later releases, so a control can be traced from the law to the system and back.

## What changed in version 3

- Rule 6(1) is split into its seven safeguards, (a) to (g).
- Three rows added: exemptions under Section 17, including Section 17(1)(f) for loan defaulters; Section 38 (conflict with other laws); and Section 44(2) (omission of Section 43A of the Information Technology Act).
- New column *Provisions covered in this row*, and the new `Coverage` sheet.
- Corrections to the legal text of Sections 8(11), 11(2) and 12(2), and the Illustrations under Rules 8(3) and 10 added.
- Every line of the `Coverage` sheet was reviewed independently against the Gazette text on 15 October 2026. The corrections are listed in the `Identifier Change Log` and in the v0.1.3 release notes.

No identifier from version 2 was removed or renamed. The `Identifier Change Log` sheet records each change.

## Limitations

- The workbook reflects the Act and the Rules as notified on 13 November 2025, read with the Removal of Difficulties Order of 5 October 2026. Check for later amendments and notifications.
- The dates on which sections of the Act come into force are taken from the Government's notification G.S.R. 843(E) of 13 November 2025. The dates for the Rules come from Rule 1 of the Rules.
- It does not cover sector rules, such as those of the Reserve Bank of India, the Insurance Regulatory and Development Authority of India, or CERT-In. These will be addressed where they overlap with DPDP in later releases.
- It is not legal advice.
