# DPDP in Practice: Release 1 Guide

**Release 1: Foundations, and know what you hold.**

Edition of 26 October 2026, for Release 1 (`v0.2.0`). Start this guide only when the **Setup Guide** checkpoint (Part 10.2) is complete. The commands follow the same layout as the setup guide: one command per grey box, numbered in order, a backslash `\` where a command continues on the next line, and values in angle brackets to replace with your own. Read "Before you start" in the setup guide first, if you have not.

Release 1 builds the model company in your workload account, loads it with synthetic customers, checks the personal data register against it, and runs the fourteen tests that store their own evidence. Step 7 removes what it created.

Start every working session with these two commands:

```bash
cd ~/work/dpdp-on-aws && source .venv/bin/activate
```
```bash
aws sso login --sso-session dpdp
```

## What Release 1 proves

| DPDP provision | What the system does | Test |
|---|---|---|
| Section 4; Section 7 | Every category of personal data has a recorded purpose and legal basis; a data flow without one is blocked | T1, T3 |
| Section 8(1) | The company knows what it holds, where, why and who receives it, and the register matches the real account | T2, T4 |
| Rule 6(1)(c) | The organisation trail cannot be stopped | T5f |
| Rule 6(1)(e) | Logs cannot be deleted, shortened or weakened, even by an administrator | T5a to T5e |
| Rule 6(1)(b) | Nobody signs in with stored passwords or keys | T7 |
| Section 16 (and RBI's rule on payment data) | Storage cannot be created outside Mumbai | T6 |

## Names and values used in both guides

These names are used exactly as written in the setup guide, the Release 1 guide and the code. Replace only the values shown in angle brackets.

| Item | Value |
|---|---|
| Region | Asia Pacific (Mumbai), `ap-south-1`, for every DPDP resource. IAM Identity Center runs in one region: US East (N. Virginia), `us-east-1`, at starting point A, where AWS created it; Asia Pacific (Mumbai) at starting point B, where Part 3.0 enables it. This guide calls it **the Identity Center region** |
| Organisational units | `Security`, `Workloads`, `Sandbox` |
| Accounts | `dpdp-management` (the organisation's management account; at starting point A the console may show it as `<team name> Management Account`), `dpdp-log-archive` and `dpdp-audit` (Security), `dpdp-workload` (Workloads), `dpdp-sandbox` (Sandbox) |
| Accounts created by AWS, not part of the build (starting point A only) | Your project account and `Identity Delegated Admin`. Both stay at Root and stay empty |
| Account emails | `<name>+dpdp-logarchive@<domain>`, `+dpdp-audit`, `+dpdp-workload`, `+dpdp-sandbox` |
| Permission sets (IAM Identity Center) | `BreakGlassAdmin` (AdministratorAccess, 1 hour), `PlatformEngineer` (PowerUserAccess and IAMReadOnlyAccess, 4 hours), `Auditor` (ReadOnlyAccess, 4 hours), `ViewOnly` (ViewOnlyAccess, 8 hours) |
| Command-line profiles | `dpdp-mgmt-admin`, `dpdp-logarchive-admin`, `dpdp-logarchive-auditor`, `dpdp-workload-eng`, `dpdp-workload-admin`, `dpdp-sandbox-eng` |
| Terraform state buckets | `dpdp-tfstate-<account id>`, one in each account |
| Guardrail policies | `region` (deny-regions-outside-mumbai), `baseline` (baseline-protections), `buckets` (protect-log-and-evidence-buckets), `cost` (deny-costly-services) |
| Organisation trail | `dpdp-organization-trail`, created in `dpdp-management` |
| Log and evidence buckets (in `dpdp-log-archive`) | `dpdp-cloudtrail-logs-<id>` (governance, 365 days), `dpdp-evidence-live-<id>` (compliance, 30 days), `dpdp-evidence-sandbox-<id>` (governance, 1 day) |
| Model company | Fernleaf Finance (fictional), an Indian lender with a prepaid wallet |
| Model company stores | `dpdp-customers`, `dpdp-loans`, `dpdp-wallet-transactions`, `dpdp-support-tickets`, `dpdp-bureau-reports-<id>`, `dpdp-app-events-<id>` |
| Test customer | `C-TEST-0001` (adult borrower), `C-TEST-0002` (teen linked to C-TEST-0001) |
| Local files never committed | `backend.hcl`, `terraform.tfvars`, `config/local.env`, `~/.aws/config`, `data/`, `evidence/`, and the bootstrap log with its saved outputs and screenshots: `notes/bootstrap-log.md`, `notes/outputs/`, `notes/screenshots/` |

---

## Step 1. Deploy Fernleaf Finance's data stores

The model company is **Fernleaf Finance (fictional)**, an Indian lender with a prepaid wallet. The name appears only in text (the register and the guides); AWS resource names stay generic, such as `dpdp-customers`, so the name can change without touching any infrastructure. Its personal data lives in four DynamoDB tables and two S3 buckets. Each store carries two tags: `DataClass = personal` and `RegisterStore = <its id in the register>`. Test T2 relies on these tags.

1. Go to the model company stack for the workload account:
   ```bash
   cd terraform/live/workload/model-company
   ```
2. Create the backend file:
   ```bash
   cp backend.hcl.example backend.hcl
   ```
3. Open it and paste the workload account's two lines from the setup guide (Part 6, step 2). Save and close.
   ```bash
   nano backend.hcl
   ```
4. Initialise:
   ```bash
   terraform init -backend-config=backend.hcl
   ```
5. Prepare the plan. It adds 4 tables, 2 buckets and, for each bucket, encryption, ownership controls and a public access block (12 resources).
   ```bash
   terraform plan -out=mc.tfplan
   ```
6. Apply it:
   ```bash
   terraform apply mc.tfplan
   ```
7. Show what was created:
   ```bash
   terraform output
   ```
8. Return to the repository folder:
   ```bash
   cd ~/work/dpdp-on-aws
   ```

**Check:** list everything tagged as personal data. Six resources must be listed. The tag search can take a few minutes to show new resources; if fewer than six appear, wait five minutes and run it again.

```bash
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=DataClass,Values=personal \
  --profile dpdp-workload-eng --query 'ResourceTagMappingList[].ResourceARN'
```

---

## Step 2. Load the synthetic customers

**Why:** The tests need realistic data to work on. All of it is synthetic, generated by the tool, so no real person's data is ever used.

1. Generate the customers and load them into the six stores:
   ```bash
   python tools/generate_synthetic_data.py --out data/ --load \
     --profile dpdp-workload-eng
   ```

It writes about 200 customers, their loans, wallet transactions, support tickets, credit bureau reports and app activity, both to `data/` on your laptop (ignored by Git) and into the six stores.

**Nothing in this data can belong to a real person:**

- Aadhaar numbers deliberately fail the Aadhaar check digit, so none can be an issued number.
- PANs use `X` as the fourth character, which is not a valid PAN holder type.
- Mobile numbers start `+91-0000`, which no Indian mobile number does.
- Emails use `example.com`, and IP addresses use the ranges reserved for documentation.

Two fixed customers are used in every test: `C-TEST-0001` (an adult borrower with an overdue instalment) and `C-TEST-0002` (a teen account linked to `C-TEST-0001`, used in Release 6).

**Check:**

2. Read the test customer directly. It must print `"Test Customer One"`.
   ```bash
   aws dynamodb get-item --table-name dpdp-customers \
     --key '{"customer_id":{"S":"C-TEST-0001"}}' \
     --profile dpdp-workload-eng --query 'Item.full_name.S'
   ```

The table's `ItemCount` in the console is refreshed by AWS only about every six hours, so it can show 0 for a while. The direct read above is immediate.

---

## Step 3. Review the personal data register

Open `register/personal-data-register.yaml`. It has three parts.

| Part | What it holds |
|---|---|
| `stores` | The six stores, with their real names (`{account_id}` is filled in automatically) |
| `vendors` | Six vendors: KYC provider, credit information company, payment gateway, SMS and WhatsApp provider, collections call centre, email provider. Each has a role, a location and a contract clause reference |
| `data_categories` | Ten categories of personal data. Each has the description that will appear in the notice (Release 4), the fields, the stores, the purposes with their legal basis and vendors, the retention rule with its legal reason, and whether it concerns children |

1. Run the check. Expected result: `PASS (0 failures, 6 warnings to review)`.
   ```bash
   python tools/register_check.py
   ```

The warnings are deliberate, and each needs a recorded decision:

| Warning | What it means | Decision to record now |
|---|---|---|
| Section 16: email provider in Ireland | Transfers outside India are allowed unless the Government restricts that country | No country has been restricted as of the date of the check; review when any notification is issued |
| Section 8(7): five retention periods not confirmed | KYC, loan, repayment, bureau and wallet records use 5 years as a placeholder | To be confirmed against the anti-money-laundering record rules and RBI directions before Release 7 |

2. Record the first decision in the bootstrap log:
   ```bash
   scripts/log_step.sh R1.3 \
     "Decision: email provider in Ireland accepted; no country restricted under s.16"
   ```
3. Record the second:
   ```bash
   scripts/log_step.sh R1.3 \
     "Decision: 5-year retention placeholders to be confirmed before Release 7"
   ```

---

## Step 4. Compare the register with the account

**Why:** A register is useful only if it matches what actually exists. This check finds personal data stored somewhere the register does not know about, and register entries for stores that do not exist.

1. Run the live check. It also confirms that every store in the register exists in the account, and that every resource tagged `DataClass = personal` is in the register. Expected result: still `PASS`.
   ```bash
   python tools/register_check.py --live --profile dpdp-workload-eng
   ```

**See the failure once**

2. Choose a name for an untracked bucket:
   ```bash
   B=dpdp-untracked-export-$RANDOM
   ```
3. Create it:
   ```bash
   aws s3api create-bucket --bucket $B --region ap-south-1 \
     --create-bucket-configuration LocationConstraint=ap-south-1 \
     --profile dpdp-workload-eng
   ```
4. Tag it as personal data, without adding it to the register:
   ```bash
   aws s3api put-bucket-tagging --bucket $B \
     --tagging 'TagSet=[{Key=DataClass,Value=personal}]' --profile dpdp-workload-eng
   ```
5. Wait five minutes, because the tag search takes a few minutes to see a new bucket:
   ```bash
   sleep 300
   ```
6. Run the live check again. It must report `FAIL [Section 8(1)] ... not in the register`.
   ```bash
   python tools/register_check.py --live --profile dpdp-workload-eng
   ```
7. Delete the bucket:
   ```bash
   aws s3api delete-bucket --bucket $B --profile dpdp-workload-eng
   ```

The tag search also keeps listing a deleted bucket for a few minutes. Wait about five minutes before running the tests in Step 6, or T2 will report this bucket.

---

## Step 5. The customer summary

**Why:** Under Section 11, a person may ask what data a company holds about them. The summary shows that Fernleaf Finance (fictional) can answer that question for one customer, from the register and the stores, with one command.

1. Full view. It lists nine categories; for each, where the data is held, the fields (Aadhaar, PAN and mobile masked), the purpose, the legal basis, the vendors with their location, and until when the data is kept.
   ```bash
   python tools/customer_summary.py --customer C-TEST-0001 --profile dpdp-workload-eng
   ```
2. Brief view, one line per category:
   ```bash
   python tools/customer_summary.py --customer C-TEST-0001 \
     --profile dpdp-workload-eng --brief
   ```

This is the foundation of the summary a company must give on request under Section 11(1). Release 10 turns it into the response to an access request.

---

## Step 6. Run the tests and check the evidence

**Why:** Each test attempts something the law requires to be true, or something it requires to be impossible, and records the result as evidence. The evidence is what an auditor or the Data Protection Board would ask to see.

### 6.1 Local configuration

**Why:** The tests need the names of your buckets, your trail and your profiles. They are kept in `config/local.env`, on the laptop only, because they contain account details.

1. Create the local settings file from its template:
   ```bash
   cp config/local.env.example config/local.env
   ```
2. Open it:
   ```bash
   nano config/local.env
   ```
3. Replace the example account ids in the four lines below with your own, and keep every other line as it is, including `DPDP_TARGET=workload`. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.

   **File content** (the four lines to change):
   ```
   DPDP_CLOUDTRAIL_BUCKET=dpdp-cloudtrail-logs-<log archive id>
   DPDP_EVIDENCE_LIVE_BUCKET=dpdp-evidence-live-<log archive id>
   DPDP_EVIDENCE_SANDBOX_BUCKET=dpdp-evidence-sandbox-<log archive id>
   DPDP_TRAIL_ARN=arn:aws:cloudtrail:ap-south-1:<management id>:trail/dpdp-organization-trail
   ```
   The bucket names and the trail ARN are in the outputs saved in the setup guide, Parts 7.1 and 7.2. To see them, run this before opening the file:
   ```bash
   cat notes/outputs/*part-7.1.txt notes/outputs/*part-7.2.txt
   ```

### 6.2 Run

**Why:** Offline tests check files only. Live tests act in your AWS accounts and write their evidence to the locked evidence bucket.

1. Offline tests (T1, T3 and the offline part of T4):
   ```bash
   python -m pytest
   ```
2. All tests, including those against AWS:
   ```bash
   python -m pytest --live -v -s
   ```

| Test | Control | Account and role | What it attempts | Pass means |
|---|---|---|---|---|
| T1 | DPDP-Act-S4 | none (offline) | Check the register | No failures |
| T2 | DPDP-Act-S8(1) | workload, PlatformEngineer | Compare the register with tagged resources | They match |
| T3 | DPDP-Act-S4 | none (offline) | Check a register with a flow that has no legal basis | Blocked, citing Section 4 |
| T4 | DPDP-Act-S8(1) | offline and workload | Summarise `C-TEST-0001` | Nine categories, vendors listed, Aadhaar masked |
| T5a | DPDP-Rule-6(1)(e) | log archive, BreakGlassAdmin | Delete a log file without a version id | Refused, and no delete marker created |
| T5b | DPDP-Rule-6(1)(e) | same | Delete a specific version of a log file | Refused |
| T5c | DPDP-Rule-6(1)(e) | same | Shorten the bucket's retention to 1 day | Refused |
| T5d | DPDP-Rule-6(1)(e) | same | Suspend versioning | Refused |
| T5e | DPDP-Rule-6(1)(e) | same | Delete the log bucket | Refused |
| T5f | DPDP-Rule-6(1)(c) | same | Stop the organisation trail | Refused |
| T6 | DPDP-Act-S16 | workload, PlatformEngineer | Create a bucket in Singapore | Refused |
| T7 | DPDP-Rule-6(1)(b) | workload and log archive | List IAM users | None exist |

Expected: `14 passed`. If T5 tests are skipped with "No log file delivered yet", wait 15 minutes after creating the trail and run step 2 again.

### 6.3 Check the evidence

Each live test prints the location and the S3 version id of its evidence record. Each record contains the control, the time in IST, what was attempted, the response from AWS, the outcome, the Git commit of the test code, and a SHA-256 checksum.

What proves a record is unchanged is the bucket itself: Object Lock in compliance mode, and a single version of the object. The checksum lets anyone detect a change in a copy taken out of the bucket, for example one attached to an audit report.

1. Load the bucket names from your settings file into the terminal:
   ```bash
   set -a; source config/local.env; set +a
   ```
2. List the latest evidence records:
   ```bash
   aws s3 ls s3://$DPDP_EVIDENCE_LIVE_BUCKET/ --recursive \
     --profile dpdp-logarchive-auditor | tail -15
   ```
3. Pick the latest T5a record:
   ```bash
   KEY=$(aws s3 ls s3://$DPDP_EVIDENCE_LIVE_BUCKET/dpdp-log-archive/ --recursive \
     --profile dpdp-logarchive-auditor | grep t5a | tail -1 | awk '{print $4}')
   ```
4. Download it:
   ```bash
   aws s3 cp s3://$DPDP_EVIDENCE_LIVE_BUCKET/$KEY /tmp/rec.json \
     --profile dpdp-logarchive-auditor
   ```
5. Verify its checksum. It must print `checksum valid: True`. This is one command over several lines; paste it as it is.
   ```bash
   python -c "
   import json, sys
   sys.path.insert(0, '.')
   from tools import evidence
   print('checksum valid:', evidence.verify(json.load(open('/tmp/rec.json'))))
   "
   ```
6. Show its lock. It must show `COMPLIANCE` with a date 30 days ahead.
   ```bash
   aws s3api get-object-retention --bucket $DPDP_EVIDENCE_LIVE_BUCKET --key "$KEY" \
     --profile dpdp-logarchive-auditor
   ```
7. Count its versions. It must print `1`.
   ```bash
   aws s3api list-object-versions --bucket $DPDP_EVIDENCE_LIVE_BUCKET --prefix "$KEY" \
     --profile dpdp-logarchive-auditor --query 'length(Versions)'
   ```

This is what an auditor would do: read the record with read-only access, confirm it is locked and has never been replaced, and keep the checksum to compare against any copy.

---

---

## Step 7. Remove what Release 1 created (optional)

**Why:** Do this when you have finished with Release 1, or before you remove the whole build (setup guide, Part 11). It deletes the model company's six stores with their synthetic data, and the synthetic files on your laptop. The platform from the setup guide stays as it is.

What stays: the evidence records written in Step 6 are locked in the evidence bucket for 30 days and cannot be deleted before then. They are removed with the log archive account (setup guide, Part 11). Once the stores are gone, tests T2 and T4 (live) fail if run again, because there is nothing left to check.

1. Go to the model company stack:
   ```bash
   cd terraform/live/workload/model-company
   ```
2. Destroy it. The plan it shows must read `Plan: 0 to add, 0 to change, 12 to destroy.`, all of them in this stack: 4 tables, 2 buckets and the buckets' settings. Read it, then type `yes`. The two buckets are emptied first, because their code allows it for synthetic data.
   ```bash
   terraform destroy
   ```
3. Return to the repository folder:
   ```bash
   cd ~/work/dpdp-on-aws
   ```
4. Search for anything still tagged as personal data. It must print `[]`. The tag search can keep listing deleted resources for a few minutes; if it does, wait five minutes and run it again.
   ```bash
   scripts/log_step.sh R1.7 "Model company removed; nothing tagged personal" -- \
     aws resourcegroupstaggingapi get-resources \
     --tag-filters Key=DataClass,Values=personal \
     --profile dpdp-workload-eng --query 'ResourceTagMappingList[].ResourceARN'
   ```
5. Delete the synthetic data files and the offline evidence on the laptop:
   ```bash
   rm -rf data evidence
   ```

To build Release 1 again later, start from Step 1.

---

## What Release 1 does not do

- No notice or consent yet. They arrive in Release 4.
- Changes are applied from a laptop. The approval-gated pipeline arrives in Release 2.
- Guardrails do not apply to the AWS management account; that is how AWS Organizations works. The management account holds no workloads, is protected by MFA, and any attempt to stop the trail is recorded.
- IAM Identity Center runs in one region, which AWS cannot change later. At starting point A it is US East (N. Virginia), where AWS's sign-up flow created it, so sign-in records are held there. At starting point B it is Mumbai. In both cases, all personal data of Fernleaf Finance (fictional) stays in Mumbai.
- One person holds every role. In a real organisation, a second person would approve changes.
- The retention periods for KYC, lending and wallet records are placeholders until confirmed against the source rules.
- All data is synthetic. Vendors are entries in the register; no data is sent to any real vendor.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| T2 fails: store not found | Step 1 not applied in that account, or a tag was changed. Run `terraform plan` in the model-company stack |
| T4 live finds no customer | Step 2 not run against that account's profile |
| T5 skipped | No log file yet. Wait 15 minutes after Part 7 of the setup guide |
| An evidence record shows `(with uncommitted changes)` after the commit | Files in the repository differ from the commit. Run `git status`; restore any file you did not mean to change with `git checkout <file>` |
| T5 fails with `InvalidBucketState` instead of `AccessDenied` | The `buckets` guardrail is not attached to the Security unit. Check stage C of the setup guide |
| T5f fails with `TrailNotFoundException` | `DPDP_TRAIL_ARN` in `config/local.env` has the wrong account id or region |
| T6 fails because the bucket was created | The `region` guardrail is not attached to that account's unit. The test deletes the bucket it created |
| Evidence upload fails with `AccessDenied` | The bucket policy allows each account to write only to its own folder. Check `DPDP_TARGET` and the bucket name in `config/local.env` |
| `ModuleNotFoundError: tools` | Run commands from the repository's top folder, with the virtual environment active |
