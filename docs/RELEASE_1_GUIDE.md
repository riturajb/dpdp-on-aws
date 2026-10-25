# DPDP in Practice: Release 1 Build Guide

**Release 1: Foundations, and know what you hold.**

Version of 22 October 2026. Start this guide only when the **AWS and GitHub Setup Guide** checkpoint (Part 10.3) is complete. The commands follow the same layout as the setup guide: one command per grey box, numbered in order, a backslash `\` where a command continues on the next line, and values in angle brackets to replace with your own.

> **Reading this guide outside the author's build.** It was written for the author's own build and uses his GitHub account name, `riturajb`. Use your own wherever it appears. Steps 1 to 7 build and test the release in your own AWS accounts. Steps 8 to 12 describe how the author publishes a release to this repository; you do not need them to run the release.

Start every working session with:

```bash
cd ~/work/dpdp-on-aws-workbench && source .venv/bin/activate
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
| Region | Asia Pacific (Mumbai), `ap-south-1`, for every DPDP resource. IAM Identity Center stays in the region where AWS's sign-up flow created it, normally US East (N. Virginia), `us-east-1` |
| Organisational units | `Security`, `Workloads`, `Sandbox` |
| Accounts | `dpdp-management` (the organisation's management account; the console may show it as `<team name> Management Account`), `dpdp-log-archive` and `dpdp-audit` (Security), `dpdp-workload` (Workloads), `dpdp-sandbox` (Sandbox) |
| Accounts created by AWS, not part of the build | Your project account and `Identity Delegated Admin`. Both stay at Root and stay empty |
| Account emails | `<yourname>+dpdp-logarchive@gmail.com`, `+dpdp-audit`, `+dpdp-workload`, `+dpdp-sandbox` |
| Permission sets (IAM Identity Center) | `BreakGlassAdmin` (AdministratorAccess, 1 hour), `PlatformEngineer` (PowerUserAccess and IAMReadOnlyAccess, 4 hours), `Auditor` (ReadOnlyAccess, 4 hours), `ViewOnly` (ViewOnlyAccess, 8 hours) |
| Command-line profiles | `dpdp-mgmt-admin`, `dpdp-logarchive-admin`, `dpdp-logarchive-auditor`, `dpdp-workload-eng`, `dpdp-workload-admin`, `dpdp-sandbox-eng` |
| Terraform state buckets | `dpdp-tfstate-<account id>`, one in each account |
| Guardrail policies | `region` (deny-regions-outside-mumbai), `baseline` (baseline-protections), `buckets` (protect-log-and-evidence-buckets), `cost` (deny-costly-services) |
| Organisation trail | `dpdp-organization-trail`, created in `dpdp-management` |
| Log and evidence buckets (in `dpdp-log-archive`) | `dpdp-cloudtrail-logs-<id>` (governance, 365 days), `dpdp-evidence-live-<id>` (compliance, 30 days), `dpdp-evidence-sandbox-<id>` (governance, 1 day) |
| Model company | Fernleaf Finance (fictional), an Indian lender with a prepaid wallet. Always written with "(fictional)" the first time in each post or document |
| Model company stores | `dpdp-customers`, `dpdp-loans`, `dpdp-wallet-transactions`, `dpdp-support-tickets`, `dpdp-bureau-reports-<id>`, `dpdp-app-events-<id>` |
| Test customer | `C-TEST-0001` (adult borrower), `C-TEST-0002` (teen linked to C-TEST-0001) |
| Local files never committed | `backend.hcl`, `terraform.tfvars`, `config/local.env`, `~/.aws/config`, `data/`, `evidence/`, and the bootstrap log with its saved outputs and screenshots: `notes/bootstrap-log.md`, `notes/outputs/`, `notes/screenshots/` |

---

## Step 1. Deploy Fernleaf Finance's data stores

The model company is **Fernleaf Finance (fictional)**, an Indian lender with a prepaid wallet. The name appears only in text (the register, the guides and the posts); AWS resource names stay generic, such as `dpdp-customers`, so the name can change without touching any infrastructure. Its personal data lives in four DynamoDB tables and two S3 buckets. Each store carries two tags: `DataClass = personal` and `RegisterStore = <its id in the register>`. Test T2 relies on these tags.

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
8. Return to the workbench folder:
   ```bash
   cd ~/work/dpdp-on-aws-workbench
   ```

**Check:** list everything tagged as personal data. Six resources must be listed. The tag search can take a few minutes to show new resources; if fewer than six appear, wait five minutes and run it again.

```bash
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=DataClass,Values=personal \
  --profile dpdp-workload-eng --query 'ResourceTagMappingList[].ResourceARN'
```

---

## Step 2. Load the synthetic customers

**Why:** The tests and the demonstration need realistic data to work on. All of it is synthetic, generated by the tool, so no real person's data is ever used.

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

Two fixed customers are used in every test and demonstration: `C-TEST-0001` (an adult borrower with an overdue instalment) and `C-TEST-0002` (a teen account linked to `C-TEST-0001`, used in Release 6).

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

The warnings are deliberate, and each needs a recorded decision in `notes/decisions.md`:

| Warning | What it means | Decision to record now |
|---|---|---|
| Section 16: email provider in Ireland | Transfers outside India are allowed unless the Government restricts that country | No country has been restricted as of the date of the check; review when any notification is issued |
| Section 8(7): five retention periods not confirmed | KYC, loan, repayment, bureau and wallet records use 5 years as a placeholder | To be confirmed against the anti-money-laundering record rules and RBI directions before Release 7 |

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
2. Brief view, used in the demonstration:
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
3. Fill in the bucket names from the logging stack's output (setup guide, Part 7.1, step 9), and the trail ARN with the management account id. Keep `DPDP_TARGET=workload`. Save and close.

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

## Step 7. Make the demonstration video

**Why:** The video shows, in about 70 seconds, that the release's claims hold live on AWS. It is made for the LinkedIn feed on a phone, where most people watch with the sound off: portrait format, a large caption on every screen, and only the lines that prove each point, in a font large enough to read on a phone.

**How it is made.** `scripts/demo_release1.sh` runs real commands live against your AWS accounts, the same commands a reader can type, and shows their output in the terminal as they run. It saves every command, the time it ran and its full output. `tools/demo_release1.py` then draws the video from that saved run: each command appears as if typed, then its real output appears line by line, with key words in amber. The typing is drawn afterwards, and the opening card says so: "Replayed from a live run on <date and time>. Commands and AWS responses unchanged; account ids masked". No screen recorder or video editor is needed.

**What is in the video, and what is not.** Only the scenes below. Account numbers, the organisation id, policy ids and email addresses are masked. The video never shows the AWS console, a browser, configuration files, your user name, or anything from the bootstrap log, its saved outputs or its screenshots (setup guide, Part 1.6).

| Scene | Caption | Commands shown, with their real output |
|---|---|---|
| Opening card | DPDP IN PRACTICE · Release 1. Five things this system proves, live on AWS. Replayed from a live run, with its date and time | None |
| 1 of 5 · Section 4, Section 8(1) | Know what you hold | `python tools/customer_summary.py --customer C-TEST-0001 --profile dpdp-workload-eng --compact`: each category, its legal basis and how long it is kept, and the masked Aadhaar and PAN |
| 2 of 5 · Section 4, Section 8(2) | No legal basis, no data flow | The register check on the copy with the marketing-partner flow (two `FAIL` lines, `Result: FAIL`), then on the approved register (`Result: PASS`) |
| 3 of 5 · Rule 6(1)(c), Rule 6(1)(e) | Logs that cannot be erased | `python -m pytest --live` on tests T5a to T5f: six `PASSED` lines, each meaning AWS refused the attempt, and `6 passed` |
| 4 of 5 · Design choice · Section 16 | Data stays in Mumbai | `aws s3api create-bucket` in Singapore: `AccessDenied ... with an explicit deny in a service control policy` |
| 5 of 5 · Rule 6(1)(g) | Proof that cannot be altered | The T5a evidence record just written, read back from the bucket (`control`, `time`, `outcome`, `sha256`), and its lock: `COMPLIANCE` until a date |
| Closing card | Code, tests and guide: github.com/riturajb/dpdp-on-aws. Not legal advice | None |

The footer of every scene shows the Defenaar Consulting logo, your name, and "Fernleaf Finance (fictional) · synthetic data · live run" with the date and time of the run.

**If a check does not give the expected result,** every scene carries the line **NOT FOR PUBLISHING**, and the script ends with a list of what went wrong. Fix the cause and run it again. Never publish a video with that line.

**Install the video tools (once):**

1. Install ffmpeg, which joins the screens into a video, and the fonts the screens use:
   ```bash
   sudo apt install -y ffmpeg fonts-dejavu-core
   ```
2. Install the Python packages again, which adds Pillow, the library that draws the screens:
   ```bash
   pip install -r requirements.txt
   ```

**Try it without AWS (optional):** steps 1 and 2 also run from the synthetic files of Step 2. This makes a short test video marked NOT FOR PUBLISHING.
```bash
scripts/demo_release1.sh --offline data/
```

**Make the video:**

1. Sign in:
   ```bash
   aws sso login --sso-session dpdp
   ```
   If the browser does not open by itself, copy the printed link into the Windows browser, as in the setup guide, Part 3.5, step 6.
2. Run the demonstration. It takes about a minute; tests T5 and T6 run against AWS in steps 3 and 4.
   ```bash
   scripts/demo_release1.sh
   ```
3. Read the end of the output. It must not list any problem, and it prints where the run was saved, in this form:
   ```
   Results saved in notes/demo/<date>-<time>/run.json
   Video: notes/demo/<date>-<time>/release1_demo.mp4 (about 60 seconds)
   ```
4. Open the folder from Windows: in File Explorer, open the pinned `notes` folder (setup guide, Part 1.6, step 4) → `demo` → the newest folder.
5. Play `release1_demo.mp4` once from start to end. Check that every screen shows the expected result and that no 12-digit number, email address or user name appears anywhere.
6. Copy `release1_demo.mp4` to Windows for posting, for example to your Videos folder, under the name `DPDP_in_Practice_Release_1.mp4`. Replace `<date>-<time>` with the folder name from step 3:
   ```bash
   cp notes/demo/<date>-<time>/release1_demo.mp4 \
     "/mnt/c/Users/<windows user>/Videos/DPDP_in_Practice_Release_1.mp4"
   ```

**What is kept.** Each run has its own folder in `notes/demo/`: `run.json` holds every value shown in the video, and `raw/` holds the full output of each check, including the complete AWS responses. Git ignores the folder, because the full outputs contain account ids. To make the video again from a saved run, without running the checks again:
```bash
python tools/demo_release1.py video notes/demo/<date>-<time>/run.json
```

**Optional, for step 2:** a second short clip in the browser. Open a pull request in the workbench that adds the marketing-partner flow to the register. The **Personal data register and offline tests** check turns red. Add the legal basis and contract clause, and it turns green. Record it with the Windows Snipping Tool's video mode (**Windows + Shift + R**), and check that the browser shows no account number, email address or other repository name.

---

## Step 8. Freeze the release candidate

**Why:** A signed tag fixes the exact version that was tested, so the published release can be traced back to it. The candidate is merged through a pull request, like every other change in the workbench.

1. Check what will be committed. Only files you changed in Steps 1 to 7 and `.terraform.lock.hcl` files may be listed; nothing from `notes/`, `data/` or `evidence/`, and no `backend.hcl` or `terraform.tfvars`.
   ```bash
   git status
   ```
2. Create a branch for the candidate:
   ```bash
   git checkout -b release-1-candidate
   ```
3. Commit everything:
   ```bash
   git add -A && git commit -m "Release 1 candidate"
   ```
4. Push the branch:
   ```bash
   git push -u origin HEAD
   ```
5. **Console (GitHub):** open `dpdp-on-aws-workbench` → **Compare & pull request** → **Create pull request**. When all three checks are green: **Merge pull request**, with **Create a merge commit** → **Confirm merge** → **Delete branch**.
6. Return to main and pull the merge:
   ```bash
   git checkout main && git pull
   ```
7. Create the signed candidate tag on the merged commit:
   ```bash
   git tag -s r1-rc1 -m "Release 1 candidate 1"
   ```
8. Push the tag:
   ```bash
   git push origin r1-rc1
   ```
9. Delete the branch on the laptop:
   ```bash
   git branch -d release-1-candidate
   ```

No new features after this point. Only fixes found in Steps 9 and 10.

---

## Step 9. Compose the release in the public repository

The workbench history is not copied. The release is rebuilt as small, signed commits, each one logical change with its control in the message.

1. Go to the work folder:
   ```bash
   cd ~/work
   ```
2. Clone the public repository:
   ```bash
   git clone git@github.com:riturajb/dpdp-on-aws.git
   ```
3. Go into it:
   ```bash
   cd dpdp-on-aws
   ```
4. Create the release branch:
   ```bash
   git switch -c release/1-foundations
   ```

**For each of the 17 commits in the table below:**

5. Copy each listed path from the workbench. Run this once per path, replacing `<path>` with the path from the table:
   ```bash
   cp -r ~/work/dpdp-on-aws-workbench/<path> <path>
   ```
   If the copy fails with `No such file or directory`, the folder does not exist yet in the public repository. Create it, in this form, and copy again:
   ```bash
   mkdir -p <folder>
   ```
6. Stage exactly the listed paths:
   ```bash
   git add <listed paths>
   ```
7. Confirm that only the listed files are staged:
   ```bash
   git status
   ```
8. Commit. An editor opens; write the message in the format shown after the table, save and close.
   ```bash
   git commit
   ```

| # | Files | Commit title | Control trailer |
|---|---|---|---|
| 1 | `.gitignore`, `.tflint.hcl`, `.pre-commit-config.yaml`, `requirements.txt`, `pytest.ini` | Repository: Add local checks and project configuration | None |
| 2 | `policies/scp/README.md`, `policies/scp/deny-regions-outside-mumbai.json`, `baseline-protections.json`, `deny-costly-services.json` | Foundations: Add guardrails for region, audit trail, root user and cost | DPDP-Act-S16, DPDP-Rule-6(1)(b), DPDP-Rule-6(1)(c) |
| 3 | `policies/scp/protect-log-and-evidence-buckets.json` | Foundations: Protect log and evidence buckets from deletion and weakening | DPDP-Rule-6(1)(e) |
| 4 | `terraform/modules/locked-bucket/`, `terraform/modules/account-baseline/` | Foundations: Add modules for locked buckets and account baselines | DPDP-Rule-6(1)(e), DPDP-Rule-6(1)(a) |
| 5 | `terraform/live/management/organization/`, `scripts/bootstrap_state_bucket.sh` | Foundations: Add organisation, accounts and staged guardrail attachments | DPDP-Rule-6(1)(b), DPDP-Rule-6(1)(g) |
| 6 | `terraform/live/log-archive/logging/` | Foundations: Keep logs for one year in a locked bucket | DPDP-Rule-6(1)(e) |
| 7 | `terraform/live/management/trail/` | Foundations: Record management events in every account | DPDP-Rule-6(1)(c) |
| 8 | `terraform/live/*/baseline/` | Foundations: Apply the account baseline to member accounts | DPDP-Rule-6(1)(a) |
| 9 | `terraform/live/management/cost/` | Foundations: Add monthly budget alerts | None |
| 10 | `terraform/modules/model-company/`, `terraform/live/workload/model-company/`, `terraform/live/sandbox/model-company/` | Register: Add the model company's data stores | DPDP-Act-S8(1) |
| 11 | `tools/__init__.py`, `tools/verhoeff.py`, `tools/generate_synthetic_data.py` | Register: Add synthetic data that cannot match real people | None |
| 12 | `register/personal-data-register.yaml` | Register: Add the personal data register | DPDP-Act-S4, DPDP-Act-S7, DPDP-Act-S8(1) |
| 13 | `tools/register.py`, `tools/register_check.py`, `tools/evidence.py`, `tests/__init__.py`, `tests/conftest.py`, `tests/foundations/__init__.py`, `tests/fixtures/`, `tests/foundations/test_t1_t3_register.py` | Register: Block data flows without a legal basis | DPDP-Act-S4 |
| 14 | `tools/customer_summary.py`, `tests/foundations/test_t4_customer_summary.py`, `tests/foundations/test_t2_register_matches_account.py` | Register: Show everything held about one customer | DPDP-Act-S8(1) |
| 15 | `tests/foundations/test_t5_*.py`, `test_t6_*.py`, `test_t7_*.py`, `config/local.env.example`, `config/aws-config.example` | Tests: Add guardrail tests with evidence records | DPDP-Rule-6(1)(b), DPDP-Rule-6(1)(c), DPDP-Rule-6(1)(e), DPDP-Act-S16 |
| 16 | `.github/workflows/checks.yml` | Repository: Run checks on every pull request | None |
| 17 | `scripts/demo_release1.sh`, `tools/demo_release1.py`, `tools/assets/`, `scripts/log_step.sh`, `notes/bootstrap-log.template.md` (the empty template only), `docs/SETUP_GUIDE.md`, `docs/RELEASE_1_GUIDE.md`, and from `release-docs/`: `README.md`, `CHANGELOG.md`, `docs/STANDARDS.md` (see below the table) | Docs: Add the guides, README, changelog and demonstration tool for Release 1 | None |

**Commit message format:** a title, a blank line, one or two sentences, then the trailers. **File content** example for commit 6:

```
Foundations: Keep logs for one year in a locked bucket

The organisation trail writes to a bucket with Object Lock in governance
mode and a default retention of 365 days. Evidence buckets use
compliance mode for live results and governance mode for the sandbox.

Control: DPDP-Rule-6(1)(e)
Release: 1
Tested-by: tests/foundations/test_t5_logs_cannot_be_erased.py
Approved-by: Rituraj
```

Every commit is signed automatically by the settings from the setup guide, Part 1.3.

**Commit 17: three files come from `release-docs/` and go to a different place.** The workbench keeps the public versions of the README, the changelog and the project standards in `release-docs/`, so they do not overwrite the workbench's own files. For commit 17, copy the other paths in the table as usual, then:

1. Set the release date in the changelog, in the form `27 October 2026`:
   ```bash
   sed -i "s/<release date>/<day month year>/" \
     ~/work/dpdp-on-aws-workbench/release-docs/CHANGELOG.md
   ```
2. Copy the README:
   ```bash
   cp ~/work/dpdp-on-aws-workbench/release-docs/README.md README.md
   ```
3. Copy the changelog:
   ```bash
   cp ~/work/dpdp-on-aws-workbench/release-docs/CHANGELOG.md CHANGELOG.md
   ```
4. Copy the project standards:
   ```bash
   cp ~/work/dpdp-on-aws-workbench/release-docs/STANDARDS.md docs/STANDARDS.md
   ```

Then stage and commit as in steps 6 to 8 above. If the release slips past the date set in item 1, change the date in `CHANGELOG.md` in the public repository before Step 11.

**After commit 17**

9. Run the local checks once more:
   ```bash
   terraform fmt -check -recursive terraform \
     && python tools/register_check.py && python -m pytest
   ```
10. Push the branch:
    ```bash
    git push -u origin release/1-foundations
    ```
11. On GitHub, open a pull request into `main` titled `Release 1: Foundations, and know what you hold`. Paste the checklist from Step 11 into its description. Wait for the three checks to pass.
12. Now that the checks have run once, make them required: **Settings → Rules → Rulesets → protect-main →** tick **Require status checks to pass** and add `Terraform format, validate and lint`, `Secrets and misconfiguration scan` and `Personal data register and offline tests`. Save.

---

## Step 10. Clean-room test in the sandbox

This tests what will be published, from the release branch, in an account where nothing of Fernleaf Finance exists yet. Open a **new terminal** for this step, so that no value from Step 6 is left in the shell.

1. Go to the public repository (on `release/1-foundations`):
   ```bash
   cd ~/work/dpdp-on-aws
   ```
2. Create and switch on its own virtual environment:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```
3. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Go to the sandbox model company stack:
   ```bash
   cd terraform/live/sandbox/model-company
   ```
5. Create the backend file:
   ```bash
   cp backend.hcl.example backend.hcl
   ```
6. Open it and paste the sandbox account's two lines (setup guide, Part 6, step 3). Save and close.
   ```bash
   nano backend.hcl
   ```
7. Initialise:
   ```bash
   terraform init -backend-config=backend.hcl
   ```
8. Prepare the plan:
   ```bash
   terraform plan -out=sb.tfplan
   ```
9. Apply it:
   ```bash
   terraform apply sb.tfplan
   ```
10. Return to the repository's top folder:
    ```bash
    cd ~/work/dpdp-on-aws
    ```
11. Load the synthetic customers into the sandbox:
    ```bash
    python tools/generate_synthetic_data.py --out data/ --load \
      --profile dpdp-sandbox-eng
    ```
12. Copy your local settings from the workbench:
    ```bash
    cp ~/work/dpdp-on-aws-workbench/config/local.env config/local.env
    ```
13. Point the tests at the sandbox:
    ```bash
    sed -i 's/^DPDP_TARGET=.*/DPDP_TARGET=sandbox/' config/local.env
    ```
14. Run all tests. Expected: `14 passed`, with evidence written to `dpdp-evidence-sandbox-<id>` (kept for one day).
    ```bash
    python -m pytest --live -v
    ```

**Remove the sandbox copy and confirm nothing is left**

15. Go to the sandbox stack:
    ```bash
    cd terraform/live/sandbox/model-company
    ```
16. Destroy it. Read the plan it shows, then type `yes`.
    ```bash
    terraform destroy
    ```
17. Return to the repository's top folder:
    ```bash
    cd ~/work/dpdp-on-aws
    ```
18. Search for anything still tagged as personal data. It must print `[]`. The tag search can keep listing deleted resources for a few minutes; if it does, wait five minutes and run it again.
    ```bash
    aws resourcegroupstaggingapi get-resources \
      --tag-filters Key=DataClass,Values=personal \
      --profile dpdp-sandbox-eng --query 'ResourceTagMappingList[].ResourceARN'
    ```

**Confirm the published code matches what is running**

In each of these folders, copy `backend.hcl` and `terraform.tfvars` (where one exists) from the same folder in the workbench, run `terraform init -backend-config=backend.hcl`, then `terraform plan`. It must report **No changes**:

- `terraform/live/management/organization`
- `terraform/live/management/trail`
- `terraform/live/management/cost`
- `terraform/live/log-archive/logging`
- `terraform/live/log-archive/baseline`, `terraform/live/workload/baseline`, `terraform/live/sandbox/baseline`
- `terraform/live/workload/model-company`

If a plan shows a change, the published code differs from what was deployed. Fix the branch before merging.

---

## Step 11. Merge and prepare the release

**Why:** The checklist confirms, in one place, that everything the release claims has been tested and recorded before anything is published.

### Release checklist (paste into the pull request)

- [ ] Every commit is signed and carries a `Control` trailer
- [ ] The three pull request checks pass
- [ ] Clean-room test in the sandbox: 14 passed
- [ ] The sandbox copy was destroyed and the tag search returns nothing
- [ ] Every shared stack plans with no changes
- [ ] `gitleaks detect --source .` reports nothing, and no file contains an account number, email address or real personal data
- [ ] Demonstration video made from a live run with no problem listed, and no account number visible
- [ ] Monthly cost so far checked in Billing (expected: close to zero)
- [ ] Release documents written: README section, public Release 1 guide, `CHANGELOG.md` entry
- [ ] Simulated parts labelled as simulated; limitations stated

1. Merge the pull request with **Create a merge commit**, titled `Release 1: Foundations, and know what you hold`.
2. Draft the GitHub release, without publishing: **Releases → Draft a new release**, type the tag name `v0.2.0` (the signed tag itself is created in Step 12), target `main`, title `Release 1: Foundations, and know what you hold`. For the release notes, print the prepared text in the workbench, copy it, and paste it into the description:
   ```bash
   cat ~/work/dpdp-on-aws-workbench/release-docs/RELEASE_NOTES_v0.2.0.md
   ```
   Before saving the draft, check that every statement in it is true for this release; in particular, keep "All fourteen tests passed in a clean-room run" only if Step 10 passed.

---

## Step 12. Publish

**Why:** Publishing makes the release available to readers, with a signed tag that ties it to the tested code.

1. Go to the public repository:
   ```bash
   cd ~/work/dpdp-on-aws
   ```
2. Switch to `main`:
   ```bash
   git switch main
   ```
3. Bring it up to date with the merge:
   ```bash
   git pull
   ```
4. Create the signed release tag:
   ```bash
   git tag -s v0.2.0 -m "Release 1: Foundations, and know what you hold"
   ```
5. Push the tag:
   ```bash
   git push origin v0.2.0
   ```
6. On GitHub, open the draft release, select the existing tag `v0.2.0`, and publish.
7. Publish the LinkedIn post with the demonstration video, labelled `DPDP in Practice · Release 1`.
8. In the workbench, record the release date and the published commit in `notes/releases.md`.

---

## What Release 1 does not do (stated in its guide)

- No notice or consent yet. They arrive in Release 4.
- Changes are applied from a laptop. The approval-gated pipeline arrives in Release 2.
- Guardrails do not apply to the AWS management account; that is how AWS Organizations works. The management account holds no workloads, is protected by MFA, and any attempt to stop the trail is recorded.
- IAM Identity Center runs in US East (N. Virginia), where AWS's sign-up flow created it, and AWS cannot move it. Sign-in records are held there; all personal data of Fernleaf Finance (fictional) stays in Mumbai.
- One person holds every role. In a real organisation, a second person would approve changes.
- The retention periods for KYC, lending and wallet records are placeholders until confirmed against the source rules.
- All data is synthetic. Vendors are entries in the register; no data is sent to any real vendor.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| T2 fails: store not found | Step 1 not applied in that account, or a tag was changed. Run `terraform plan` in the model-company stack |
| T4 live finds no customer | Step 2 not run against that account's profile |
| T5 skipped | No log file yet. Wait 15 minutes after Part 7 of the setup guide |
| T5 fails with `InvalidBucketState` instead of `AccessDenied` | The `buckets` guardrail is not attached to the Security unit. Check stage C of the setup guide |
| T5f fails with `TrailNotFoundException` | `DPDP_TRAIL_ARN` in `config/local.env` has the wrong account id or region |
| T6 fails because the bucket was created | The `region` guardrail is not attached to that account's unit. The test deletes the bucket it created |
| Evidence upload fails with `AccessDenied` | The bucket policy allows each account to write only to its own folder. Check `DPDP_TARGET` and the bucket name in `config/local.env` |
| `ModuleNotFoundError: tools` | Run commands from the repository's top folder, with the virtual environment active |
