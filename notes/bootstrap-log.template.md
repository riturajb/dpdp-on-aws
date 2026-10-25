# Bootstrap log

This is the record of every step that Terraform and the tests cannot record themselves: console clicks, settings checked by eye, values the guides ask you to keep, and decisions taken along the way. It is the evidence for the bootstrap of the platform.

**Private.** This file, `notes/outputs/` and `notes/screenshots/` contain account ids and email addresses. Git ignores them, so they never reach either repository. Keep a backup copy outside the laptop (setup guide, Part 1.6).

**How to fill it in** (setup guide, Part 1.6):

- Write each value in the tables below as you reach that part of the setup guide.
- For a command whose output proves a step, run it through `scripts/log_step.sh` with `--`. The output is saved in `notes/outputs/`, and a line is added to the activity log at the end of this file.
- For a console page that is the only proof of a step, save a screenshot in `notes/screenshots/`, named `<part>-<what it shows>.png`, for example `5.3-root-credentials-not-present.png`, and log it with `scripts/log_step.sh`.
- Decisions about the personal data register go in `notes/decisions.md` (Release 1 guide, Step 3), not here.

---

## Part 2. Management account

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 2.1 | Default region set to Asia Pacific (Mumbai) | | |
| 2.2 | Root user MFA device assigned (device name, not the code) | | |
| 2.3 | Root access keys: none exist | | |
| 2.4 | Alternate contacts added (Billing, Operations, Security) | | |
| 2.5 | IAM access to billing activated | | |
| 2.6 | Plan shown in Billing (Paid plan expected) | | |

## Part 3. Organisation and sign-in

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 3.1 | Organisation id | | |
| 3.1 | Management account id | | |
| 3.1 | Project account name and id (created by AWS) | | |
| 3.1 | Identity Delegated Admin account id (created by AWS) | | |
| 3.1 | Policy types enabled (SCP, RCP) | | |
| 3.2 | Service control policies attached to Root (names) | | |
| 3.2 | Resource control policies attached to Root (names) | | |
| 3.2 | Policy containing `RegionFloor` attached to Root: yes or no, and action taken | | |
| 3.3 | IAM Identity Center primary region | | |
| 3.3 | AWS access portal URL (Dual-stack) | | |
| 3.3 | Identity source (AWS Builder ID expected) | | |
| 3.3 | Builder ID MFA registered | | |
| 3.4 | Multi-account permissions enabled | | |
| 3.4 | Permission sets created: BreakGlassAdmin, Auditor, ViewOnly, PlatformEngineer | | |
| 3.4 | BreakGlassAdmin assigned to the management account | | |
| 3.5 | Sign-in check: `Arn` contains `AWSReservedSSO_BreakGlassAdmin` (save output) | | |
| 3.5 | Trusted services before Part 4 (save output) | | |

## Part 4. Member accounts

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 4.1 | State bucket of the management account | | |
| 4.2 | Account limit raised by AWS (support case number and date), if needed | | |
| 4.2 | Plan summary line (`Plan: … to import, … to add, … to change, … to destroy`) | | |
| 4.2 | `dpdp-log-archive` account id | | |
| 4.2 | `dpdp-audit` account id | | |
| 4.2 | `dpdp-workload` account id | | |
| 4.2 | `dpdp-sandbox` account id | | |

## Part 5. Access to the new accounts

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 5.1 | Permission sets assigned as in the Part 5.1 table; all four show Provisioned | | |
| 5.2 | Five profile checks, each showing the right account and permission set (save output) | | |
| 5.3 | Root access management enabled | | |
| 5.3 | Root credentials of the four member accounts: Not present (screenshot) | | |

## Part 6. State buckets and baselines

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 6.1 to 6.3 | State bucket of each member account | | |
| 6.4 to 6.12 | Baseline applied in log archive, workload and sandbox (3 resources each) | | |
| 6.13 | Public access block in the workload account: all four `true` (save output) | | |
| 6.14 | Default disk encryption in the workload account: `true` (save output) | | |

## Part 7. Logging and evidence

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 7.1 | Log bucket, live evidence bucket and sandbox evidence bucket names | | |
| 7.2 | Organisation trail name and ARN | | |
| 7.3 | Trail is logging: `true` (save output) | | |
| 7.3 | Log bucket lock: governance mode, 365 days (save output) | | |

## Part 8. Cost alerts

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 8 | Budget `dpdp-monthly` created, USD 18, four alerts | | |
| 8 | Cost Anomaly Detection: monitor and alert subscription | | |

## Part 9. Guardrails

| Step | What to record | Value or result | Date |
|---|---|---|---|
| Stage A | Attached to Sandbox; Singapore refused, Mumbai allowed (save output) | | |
| Stage B | Attached to Workloads; same test (save output) | | |
| Stage C | Attached to Security; log file and bucket deletion refused (save output) | | |

## Part 10. GitHub

| Step | What to record | Value or result | Date |
|---|---|---|---|
| 10.1 | Ruleset `protect-main` active; merge commits only; Actions settings; secret scanning on | | |

## Decisions and deviations

Anything done differently from the guide, and why.

| Date | Part | What was decided | Why |
|---|---|---|---|
| | | | |

---

## Activity log

Entries added by `scripts/log_step.sh`. Times are in IST.

| Date and time | Part | What was done and why | Saved output |
|---|---|---|---|
