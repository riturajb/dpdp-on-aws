# How to use the DPDP Obligations Matrix

The workbook `DPDP_Obligations_Matrix.xlsx` is designed for a first gap assessment against the Digital Personal Data Protection Act, 2023 and the Digital Personal Data Protection Rules, 2025.

## Steps

1. **Open the `Start Here` sheet** and read the instructions.
2. **Go to `Obligations Matrix`.** Each row is one legal duty.
3. **Filter on `Applies to`.** Rows marked for Significant Data Fiduciaries, Consent Managers or other categories may not apply to your organisation. Mark these as *Not applicable to this organisation*.
4. **Fill in the yellow columns** for each remaining row:
   - **Status**: Not assessed, Not started, Partially in place, In place, or Not applicable to this organisation
   - **Owner**: the person accountable for the duty
   - **Evidence**: where proof of the control can be found
   - **Notes**: gaps, decisions or dependencies
5. **Read the exact legal text** for any row by selecting *Read the exact text*. It opens the matching row in the `Legal Text` sheet.
6. **Review `Gap Summary`.** Counts by status and priority update automatically.
7. **Use `Event Playbook`** to check that your organisation has a defined response, an owner and a time limit for each event, such as a breach or an erasure request.
8. **Use `Timeline`** to plan work against the commencement dates.

## Priority

Priority is calculated from the maximum penalty attached to the duty and the time remaining before it comes into force. Priority 1 should be addressed first.

## Control identifiers

Identifiers follow the law itself, for example:

| Identifier | Meaning |
|---|---|
| `DPDP-Act-S8(6)` | Digital Personal Data Protection Act, 2023, Section 8(6) |
| `DPDP-Rule-7(2)` | Digital Personal Data Protection Rules, 2025, Rule 7(2) |

The same identifiers will be used in the code, the tests and the evidence in later releases, so a control can be traced from the law to the system and back.

## Limitations

- The workbook reflects the Act and the Rules as notified on 13 November 2025, read with the Removal of Difficulties Order of 5 October 2026. Check for later amendments and notifications.
- It does not cover sector rules, such as those of the Reserve Bank of India, the Insurance Regulatory and Development Authority of India, or CERT-In. These will be addressed where they overlap with DPDP in later releases.
- It is not legal advice.
