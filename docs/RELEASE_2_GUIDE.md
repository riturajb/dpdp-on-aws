# DPDP in Practice: Release 2 Guide

**Release 2: Find.**

Edition for Release 2 (`v0.3.0`). Start this guide only when the **Release 1 Guide** is complete: the model company's stores exist in your workload account, the synthetic customers are loaded (Release 1 Guide, Steps 1 and 2), and the Release 1 tests pass. The commands follow the same layout as the other guides: one command per grey box, numbered in order, a backslash `\` where a command continues on the next line, and values in angle brackets to replace with your own.

Release 1 compared the personal data register with the stores **tagged** as holding personal data. Tags show only what someone remembered to label. Release 2 adds a scanner that reads every bucket, table and log group in the account, tagged or not, finds Aadhaar numbers, PANs, mobile numbers and email addresses, and compares every finding with the register. You plant three realistic problems, watch the Release 1 check miss them, watch the scanner find them, run four new tests, and remove the problems again (Step 7).

Start every working session with these two commands:

```bash
cd ~/work/dpdp-on-aws && source .venv/bin/activate
```
```bash
aws sso login --sso-session dpdp
```

## What Release 2 proves

| DPDP provision | What the system does | Test |
|---|---|---|
| Section 8(1) | Personal data is found wherever it sits in the account, tagged or not, and each finding is compared with the register | T8, T9, T10 |
| Rule 6(1)(a) | Identifiers written into logs are found, so they can be removed, masked or replaced by tokens | T11 |

## How the scanner decides

The scanner looks for four kinds of identifier, and rates each match:

| Identifier | High confidence | Medium confidence |
|---|---|---|
| Aadhaar number | 12 digits, passes the Verhoeff check digit | 12 digits in Aadhaar format, fails the check digit |
| PAN | Valid format and a valid holder type (fourth character) | Valid format, invalid holder type |
| Mobile number | 10 digits starting 6 to 9 | `+91` followed by a number no Indian mobile uses |
| Email address | Any address | Not used |

Medium matches are reported, not ignored. A mistyped Aadhaar number in a call-centre note is still a customer's personal data. All the synthetic data in this project is generated to fail these checks, so every synthetic identifier is a medium match.

Each finding then gets one of three verdicts:

| Verdict | Meaning |
|---|---|
| expected | A store in the register, holding the identifier in a field the register lists |
| unexpected category | A store in the register, holding an identifier the register does not list there |
| unregistered store | A store the register does not know about |

The report holds masked values only, such as `XXXX XXXX 1079`. It holds no hashes of identifiers either: a 12-digit Aadhaar number can be recovered from its hash by trying every possible number.

## What Release 2 adds

| Item | Value |
|---|---|
| New command-line profile | `dpdp-workload-auditor`: the `Auditor` permission set (ReadOnlyAccess) in `dpdp-workload` |
| New setting in `config/local.env` | `DPDP_PROFILE_AUDITOR=dpdp-workload-auditor` |
| Planted problems (synthetic) | A support ticket with an Aadhaar number in its notes; the bucket `dpdp-marketing-export-<workload id>`, with no tags; the log group `/fernleaf/loan-api` |
| Local reports | `evidence/discovery/<date>-<time>/report.md`, ignored by Git |
| Tests | 18 in total: 4 offline, 14 live |
| Template | `templates/discovery-plan.xlsx` |
| Script headers | Every script and test now opens with what it does, why, who runs it, when, what it reads and writes, and whether it changes anything in AWS |

---

## Step 1. Take Release 2

1. Bring the new code into your copy. If you made your own copy on GitHub (setup guide, Part 1.4), use `git pull upstream main` instead.
   ```bash
   git pull
   ```
2. Install the Python packages, in case they changed:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the offline tests. They must report `4 passed, 14 skipped`.
   ```bash
   python -m pytest
   ```

---

## Step 2. Read-only access for the scanner

**Why:** The scanner only reads. It needs to read the contents of buckets, tables and logs, and nothing else, so it runs as `Auditor` (ReadOnlyAccess), not as an engineer who can change things. `ViewOnly` would not do: it can see that a bucket exists, but not read what is in it. The `Auditor` permission set was assigned to the workload account in the setup guide, Part 5.1.

1. Check whether the profile is already there. If you set up the platform after Release 2 was published, the template in the setup guide, Part 3.5, already included it.
   ```bash
   grep -c "profile dpdp-workload-auditor" ~/.aws/config
   ```
   If it prints `1`, go to item 5. If it prints `0`, continue with item 2.
2. Open the AWS configuration:
   ```bash
   nano ~/.aws/config
   ```
3. Add this profile at the end of the file, with your workload account id. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.

   **File content:**
   ```
   [profile dpdp-workload-auditor]
   sso_session = dpdp
   sso_account_id = <workload id>
   sso_role_name = Auditor
   region = ap-south-1
   output = json
   ```
4. Sign in again:
   ```bash
   aws sso login --sso-session dpdp
   ```
5. Check the profile. The `Arn` must contain `AWSReservedSSO_Auditor` and your workload account id.
   ```bash
   scripts/log_step.sh R2.2 "Scanner profile: Auditor in workload" -- \
     aws sts get-caller-identity --profile dpdp-workload-auditor
   ```
6. Add the profile to your local settings, unless it is already there:
   ```bash
   grep -q DPDP_PROFILE_AUDITOR config/local.env || \
     echo 'DPDP_PROFILE_AUDITOR=dpdp-workload-auditor' >> config/local.env
   ```

---

## Step 3. A first scan

**Why:** Before anything is planted, the account should hold personal data only where the register says. This scan is the baseline.

1. Run the scanner. It takes about a minute.
   ```bash
   python tools/discover.py --profile dpdp-workload-auditor
   ```
2. Read the report on screen. It must say `Problems: 0`. Under **Expected**, it lists the Aadhaar numbers, PANs, mobile numbers and email addresses in the customers table, where the register says they are.

Under **Notes**, the report points out that the customers table holds full Aadhaar numbers. Under UIDAI's circular of 18 July 2025, a lender that authenticates Aadhaar through UIDAI must keep Aadhaar numbers in an Aadhaar Data Vault. Fernleaf Finance (fictional) does not have one; see "What Release 2 does not do".

If the first scan reports problems, something in your account already holds personal data outside the register. Open the store it names and find out where the data came from before you continue.

---

## Step 4. Plant three problems: a fire drill

**Why:** A detection control is trusted only once it has been seen to catch something. "The scan found nothing" can also mean the scanner is broken. So plant known problems, show that each one is caught, and keep the evidence; auditors ask for exactly this. These three problems are synthetic, but each is one that Indian lenders meet. The engineer plants them; the scan in Step 5 runs with a different, read-only identity, as it would where the person who tests a control is not the person who owns the systems.

| Problem | How it happens | What the register knows |
|---|---|---|
| Aadhaar number in ticket notes | A collections agent verifies a customer on a call and types the full Aadhaar number into the ticket | The tickets table is registered, but not for Aadhaar numbers |
| Marketing export | The marketing team exports names, mobile numbers and email addresses to a CSV file in a new bucket for a campaign | Nothing. The bucket has no tags and is not in the register |
| Debug log | The loan application service writes full request bodies, with PAN and mobile number, into its log | Nothing. Nobody planned for personal data in the log |

1. Plant them, as `PlatformEngineer`. It prints one line for each problem.
   ```bash
   python tools/plant_findings.py --profile dpdp-workload-eng
   ```

---

## Step 5. Find them

1. Run the Release 1 check, which compares the register with the tagged stores. It still ends with `Result: PASS`: none of the three problems is tagged, so this check cannot see them. That is the point of this release.
   ```bash
   python tools/register_check.py --live --profile dpdp-workload-eng
   ```
2. Run the scanner again:
   ```bash
   python tools/discover.py --profile dpdp-workload-auditor
   ```
3. The report must now say `Problems: 5 findings in 3 stores`:

   | Verdict | Store | Field | Identifier |
   |---|---|---|---|
   | unregistered store | `/fernleaf/loan-api` | `mobile` | mobile |
   | unregistered store | `/fernleaf/loan-api` | `pan` | pan |
   | unregistered store | `dpdp-marketing-export-<workload id>` | `email` | email |
   | unregistered store | `dpdp-marketing-export-<workload id>` | `mobile` | mobile |
   | unexpected category | `dpdp-support-tickets` | `text` | aadhaar |

   The last lines of the output name the folder where the report was saved, `evidence/discovery/<date>-<time>/`. It holds `report.md` and `findings.json`, with masked values only.
4. Save the result in the bootstrap log:
   ```bash
   scripts/log_step.sh R2.5 "Discovery: three planted problems found" -- \
     python tools/discover.py --profile dpdp-workload-auditor --compact
   ```

---

## Step 6. Run the tests and check the evidence

1. Offline tests. They must report `4 passed, 14 skipped`.
   ```bash
   python -m pytest
   ```
2. All tests, including those against AWS. They must report `18 passed`.
   ```bash
   python -m pytest --live -v
   ```

The four new tests:

| Test | Control | Account and role | What it checks | Pass means |
|---|---|---|---|---|
| T8 | DPDP-Act-S8(1) | none (offline) | Detectors on sample text, and a scan of the clean synthetic data | Every identifier found and rated correctly; nothing reported inside UUIDs or ARNs; masked values show at most four digits; no problems in clean data |
| T9 | DPDP-Act-S8(1) | workload, Auditor for the scan | Aadhaar numbers outside the fields the register lists | The ticket note is found, verdict `unexpected category` |
| T10 | DPDP-Act-S8(1) | same | Every bucket, tagged or not | The marketing export is found, verdict `unregistered store` |
| T11 | DPDP-Rule-6(1)(a) | same | Every log group | PAN and mobile numbers in the debug log are found, verdict `unregistered store` |

If T9 to T11 are skipped with "The planted problems are not there", run Step 4 first.

3. Load your settings into the terminal:
   ```bash
   set -a; source config/local.env; set +a
   ```
4. List the evidence records of the new tests. Three records must be listed, one each for T9, T10 and T11.
   ```bash
   aws s3 ls s3://$DPDP_EVIDENCE_LIVE_BUCKET/dpdp-workload/ --recursive \
     --profile dpdp-logarchive-auditor | grep -E "t9-|t10-|t11-" | tail -3
   ```

Each record names what was attempted, the masked findings the scanner reported, the outcome, the Git commit of the test code and a checksum, and is locked in compliance mode for 30 days, as in Release 1.

---

## Step 7. Remove what Release 2 created

1. Remove the three planted problems:
   ```bash
   python tools/plant_findings.py --profile dpdp-workload-eng --remove
   ```
2. Scan again. It must say `Problems: 0`.
   ```bash
   python tools/discover.py --profile dpdp-workload-auditor
   ```
3. Delete the local reports, if you no longer need them:
   ```bash
   rm -rf evidence/discovery
   ```

The evidence records of Step 6 stay locked in the evidence bucket for 30 days. The `dpdp-workload-auditor` profile and the setting in `config/local.env` stay, because later releases use them.

---

## Beyond the code

The scanner finds what is in the cloud account. Most of discovery happens outside it, with people, contracts and other systems.

**1. The decision management takes**

- No new store of personal data without a register entry approved by its data owner and the DPO.
- Whether discovery is done with tools, by hand, or both, and the budget for it.
- For a lender that authenticates Aadhaar through UIDAI: whether Aadhaar numbers are kept in an Aadhaar Data Vault, and what is kept outside it.
- The cost of deciding late: notice, consent, erasure, breach response and access requests all run on the map that discovery produces. An incomplete map makes each of them incomplete.

**2. Owners**

| Activity | Data owner (business) | DPO | IT and cloud | CISO | Internal audit |
|---|---|---|---|---|---|
| Accuracy of the register for their systems | A | C | R | I | I |
| The register as a whole | C | A | R | C | I |
| Scanning | I | C | R | A | I |
| Deciding each finding that is not expected | A | R | C | C | I |
| Independent check of the cycle | I | I | I | I | A |

A: accountable. R: responsible. C: consulted. I: informed.

**3. The procedure: a quarterly cycle**

1. Interview each business process owner, using a short questionnaire.
2. Build a SaaS and vendor inventory from procurement and accounts payable. Every paid tool appears in the invoices, including those IT never approved.
3. Scan cloud stores, databases and logs.
4. Reconcile the findings with the register.
5. Record a decision for every finding that is not expected: register it, delete it or move it, with who decided and when.

The template `templates/discovery-plan.xlsx` has a sheet for each part: the system inventory, the interview questionnaire, the scan scope and the reconciliation log, with example rows for Fernleaf Finance (fictional).

**4. The evidence**

- Dated scan reports.
- The reconciliation log with each decision.
- The register's change history in Git.
- Sign-off by each data owner.

**5. Effort and cost** (indicative, for a mid-sized company with 20 to 40 systems)

- First discovery: 4 to 8 weeks for one or two people.
- Each later quarter: 1 to 2 weeks.
- Tools are optional; the procedure works by hand at first.

**6. Outside AWS**

| Where | How to find personal data there |
|---|---|
| CRM and other SaaS | Export the field definitions and reports; review custom fields and free-text notes |
| Core banking and loan management | Review the data model with the vendor |
| Email and file shares | Classification and data loss prevention in Microsoft 365 or Google Workspace |
| Spreadsheets on laptops | Interviews and endpoint tooling; the hardest source |
| Backups, archives and the SIEM | Personal data in logs is common; backups come in Release 8 |
| Copies held by vendors | The processor questionnaire and the contract clause |

## How a company would run this

This release runs the scan by hand, once, in a small account. A company would keep the same logic and change how it runs:

| Part | In this release | In a company |
|---|---|---|
| S3 | The scanner reads text files up to 5 MB | Amazon Macie for large buckets, with custom data identifiers for Aadhaar and PAN numbers so that no keyword is needed; the scanner for what Macie does not read |
| DynamoDB | A full scan of every table | Export large tables to S3 and scan the export, so the live table is not slowed down |
| CloudWatch Logs | The last 14 days of every log group | The same, on a schedule; then a data protection policy on each log group to mask identifiers as they arrive (a later release) |
| New stores | Found at the next scan | An AWS Config rule that flags any bucket or table without a `DataClass` tag within minutes (a later release) |
| Schedule | By hand | Weekly, and after each new data flow goes live, from a scheduled job with the same read-only role |
| Findings | A report on the laptop | Each finding as a ticket for the data owner, closed only with a recorded decision |
| Fire drill | Step 4, by hand | Planted problems, run after every change to the scanner, so the control is shown to still work |

The scanner itself does not change. What changes is who receives its findings and how quickly.

## What Release 2 does not do

- **Backups and snapshots are not scanned.** They come in Release 8, with erasure.
- **Names, addresses and dates of birth are not detected.** The scanner finds identifiers with a fixed format. Free-text personal data needs interviews and other methods.
- **Images, PDFs and files larger than 5 MB are not read,** and log groups are read for the last 14 days only.
- **No Aadhaar Data Vault.** The customers table of Fernleaf Finance (fictional) holds full Aadhaar numbers, all synthetic. Under UIDAI's circular of 18 July 2025, a requesting entity that authenticates Aadhaar through UIDAI must keep Aadhaar numbers in an Aadhaar Data Vault. A real lender in that position would keep the numbers there and use reference keys elsewhere.
- **Amazon Macie is not used.** It is AWS's managed option for finding sensitive data in S3, and suits large S3 estates. It reads S3 only, not tables or logs; its Aadhaar and PAN identifiers need a keyword near the number; and it costs USD 1 per GB inspected after a 30-day free trial. The scanner in this release reads all three kinds of store, needs no keyword, understands the Aadhaar check digit, and costs nothing beyond the reads.
- **Findings are not fixed automatically.** Each one needs a person's decision, recorded in the reconciliation log.
- One person holds every role. In a real organisation, the decisions above sit with the owners in the RACI.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `AccessDenied` with `dpdp-workload-auditor` | The `Auditor` permission set is not assigned to the workload account (setup guide, Part 5.1), or the profile has the wrong account id |
| `DPDP_PROFILE_AUDITOR is not set` | Step 2, item 6 was not run |
| T9 to T11 skipped: "The planted problems are not there" | Run Step 4 |
| T10 fails: export bucket not found by the scanner | The bucket is outside `ap-south-1`, or the scan ran before the upload finished. Run the scanner again |
| T11 fails: nothing found in the log group | Log events can take a minute to become readable. Wait one minute and run the tests again |
| The first scan reports problems | Something in your account holds personal data outside the register. Read the store and field named in the report, and record a decision |
| `Token has expired` | Run `aws sso login --sso-session dpdp` again |
