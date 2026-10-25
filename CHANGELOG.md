# Changelog

Every release of DPDP on AWS is listed here, newest first. Each entry states what was added or changed, and any change to the release plan.

---

## v0.2.0 · Release 1: Foundations, and know what you hold · <day month year>

### Added

- **AWS organisation** with five accounts in three organisational units: Security (log archive, audit), Workloads (workload) and Sandbox (sandbox), with the management account at Root. Sign-in through IAM Identity Center with multi-factor authentication; no IAM users or stored access keys; root credentials removed from member accounts and managed centrally.
- **Guardrails** (service control policies), attached in three stages and tested at each stage: Mumbai only; protection of the audit trail, the organisation and the root user; protection of the log and evidence buckets; denial of high-cost services.
- **Organisation trail** recording management events in every account and region, with log file validation.
- **Locked buckets** in the log archive account: logs kept for 365 days (Object Lock, governance mode); live test evidence in compliance mode; sandbox evidence for clean-room runs.
- **Account baseline** in each member account: account-level S3 public access block, default disk encryption, IAM Access Analyzer.
- **Model company** Fernleaf Finance (fictional): four DynamoDB tables and two S3 buckets, each tagged with its register entry, loaded with synthetic customers.
- **Personal data register** with checks that name the provision they enforce, run before every commit and on every pull request.
- **Customer summary**: one command lists every category of personal data held about a customer, with purpose, legal basis, vendors and retention, with Aadhaar and PAN masked.
- **Fourteen tests** (T1 to T7) with locked evidence records.
- **Pull request checks**: Terraform format, validation and lint; secret and misconfiguration scans; the register check and offline tests.
- **Guides**: the AWS and GitHub Setup Guide and the Release 1 Guide.
- **Demonstration**: a script that runs the checks live and produces the demonstration video from the results.

### Changed

- Release plan: Release 1 moved from 20 October 2026 to late October 2026, while AWS raised the organisation's account limit. Later releases moved by about one week. The plan now shows indicative timings instead of exact dates.
- README: Release 1 section added; release plan updated.
- Project standards (`docs/STANDARDS.md`): the commit message format now matches the trailers used in this repository (`Control`, `Release`, `Tested-by`, `Approved-by`), and the evidence record is described field by field as it is recorded.

### Security

- Third-party GitHub Actions are pinned to full commit identifiers, not version tags. The version tags of `aquasecurity/trivy-action` were taken over by an attacker in March 2026 and later deleted; the scan now uses v0.35.0 by commit identifier.

---

## v0.1.0 · Release 0: Blueprint · 14 October 2026

### Added

- **DPDP Obligations Matrix** (`blueprint/DPDP_Obligations_Matrix.xlsx`): a gap-analysis workbook covering the duties in the Act and the Rules, with the exact legal text, commencement dates, time limits, maximum penalties and ISO/IEC 27001:2022 Annex A references.
- **How to use the matrix** (`blueprint/HOW_TO_USE.md`).
- **Project standards** (`docs/STANDARDS.md`).

### Changed (15 October 2026)

- DPDP Obligations Matrix updated to version 3. Changes to control identifiers and rows are listed in its Identifier Change Log sheet.
