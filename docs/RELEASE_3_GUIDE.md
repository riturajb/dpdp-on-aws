# DPDP in Practice: Release 3 Guide

**Release 3: Prevent.**

Edition for Release 3 (`v0.4.0`). Start this guide only when the **Release 2 Guide** is complete: the model company's stores exist in your workload account, the synthetic customers are loaded, and the Release 2 tests pass. The commands follow the same layout as the other guides: one command per grey box, numbered in order, and a backslash `\` where a command continues on the next line. Account ids are read from your AWS sign-in; you never type one.

Release 2 found personal data after it had been stored in the wrong place, such as a marketing export in a bucket nobody tagged. Release 3 stops that kind of change before it is made, and catches it if someone makes it anyway:

- **Before a change:** every Terraform plan is checked against written rules (policy as code, in Rego, run by conftest). A plan that breaks a rule is stopped, and nothing reaches AWS.
- **After a change:** AWS Config records the data stores and log groups and checks them continuously against the same rules. A change made by hand, outside the process, is flagged within minutes.
- **Detection cannot be switched off:** a guardrail stops anyone in the workload account, including its administrator, from stopping or weakening AWS Config.

Start every working session with these two commands:

```bash
cd ~/work/dpdp-on-aws && source .venv/bin/activate
```
```bash
aws sso login --sso-session dpdp
```

## What Release 3 proves

| DPDP provision | What the system does | Test |
|---|---|---|
| Section 8(1) | No data store can be created without saying whether it holds personal data, and a personal store must be in the register | T12, T13, T14 |
| Rule 6(1)(b) | No bucket can be created without its public access block | T12, T13 |
| Rule 6(1)(d) | Personal stores can be recovered: versioning on buckets, point-in-time recovery on tables | T12, T13 |
| Rule 6(1)(e) | No log group can keep logs for less than one year | T12, T13, T14 |
| Rule 6(1)(g) | Changes made outside the process are detected, and detection cannot be stopped, even by an administrator | T14, T15 |

## The rules

The same rules are applied twice: to every plan before it is applied, and to the account continuously afterwards.

| Rule | Provision | Before the change (plan check) | After the change (AWS Config rule) |
|---|---|---|---|
| Every bucket and table carries `DataClass` (`personal` or `none`) | s.8(1) | Yes | `dpdp-store-has-dataclass` |
| A personal store carries `RegisterStore`, naming an entry in the register | s.8(1) | Yes, and the entry must exist | `dpdp-personal-store-registered` (tag present) |
| Every bucket has its public access block, all four settings on | Rule 6(1)(b) | Yes | `dpdp-bucket-not-public` |
| Personal buckets keep earlier versions | Rule 6(1)(d) | Yes | `dpdp-personal-bucket-versioned` |
| Personal tables have point-in-time recovery | Rule 6(1)(d) | Yes | `dpdp-personal-table-recoverable` |
| Log groups keep logs for at least 365 days, or never expire | Rule 6(1)(e) | Yes | `dpdp-logs-kept-one-year` |
| Every stack runs in Mumbai (`ap-south-1`) | Design choice, as in Release 1 | Yes | Already enforced by the region guardrail |

Every message from the plan check starts with its provision, for example `[R.6(1)(e)] aws_cloudwatch_log_group.debug keeps logs for 7 days`, so a blocked change explains itself.

**A tension worth knowing.** Rule 6(1)(e) asks for logs to be kept for one year, so that unauthorised access can be investigated. The debug log planted in Release 2 kept PAN and mobile numbers for 7 days. The answer is not to keep personal data in logs for a year: it is to keep the logs for a year and keep personal data out of them, by masking at the source.

## What Release 3 adds

| Item | Value |
|---|---|
| Rules (policy as code) | `policies/rego/prevent.rego`, with unit tests in `prevent_test.rego` |
| The gate | `scripts/plan_check.sh <stack> [--apply]`: plan, check, and apply only what passed |
| Tool | conftest, version pinned in `config/tool-versions.env`, installed by `scripts/install_conftest.sh` with a checksum check |
| Detective controls | `terraform/live/workload/detective`: AWS Config recorder, history bucket `dpdp-config-history-<workload id>` and six rules |
| Guardrail change | The `buckets` guardrail gains a statement that stops anyone in the workload account from stopping or weakening AWS Config |
| Model company changes | Point-in-time recovery on the four tables; versioning on the two buckets |
| Fire drill | `tools/drift_drill.py`: a bucket and a log group made by hand, flagged by AWS Config, then removed |
| Optional | `terraform/live/workload/ci-plan`: a read-only role for GitHub Actions (OpenID Connect, no stored keys) to plan and check every pull request |
| Permission change | `PlatformEngineer` gains `iam:PassRole` on the AWS Config role only (Step 4) |
| New setting in `config/local.env` | `DPDP_PROFILE_WORKLOAD_ADMIN=dpdp-workload-admin` (used only by test T15) |
| Tests | 22 in total: 5 offline, 17 live |
| Cost | A few cents a month at this size: AWS Config charges per recorded change and per rule evaluation; point-in-time recovery and versioning are charged on stored size, which is tiny here |

---

## Step 1. Take Release 3

1. Bring the new code into your copy. If you made your own copy on GitHub (setup guide, Part 1.4), use `git pull upstream main` instead.
   ```bash
   git pull
   ```
2. Install the Python packages, in case they changed:
   ```bash
   pip install -r requirements.txt
   ```
3. Install conftest. It must print `Installed: Conftest: 0.56.0` or the version named in `config/tool-versions.env`.
   ```bash
   scripts/install_conftest.sh
   ```
4. Make it available in this terminal (new terminals find it on their own):
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
5. Add the new setting, unless it is already there:
   ```bash
   grep -q DPDP_PROFILE_WORKLOAD_ADMIN config/local.env || \
     echo 'DPDP_PROFILE_WORKLOAD_ADMIN=dpdp-workload-admin' >> config/local.env
   ```
6. Run the offline tests. They must report `5 passed, 17 skipped`.
   ```bash
   python -m pytest
   ```

---

## Step 2. Mark the state buckets

**Why:** From now on, every bucket must say whether it holds personal data. The Terraform state buckets were created by a script in the setup guide, not by Terraform, so they are tagged here: `DataClass = none`. Without this, AWS Config would rightly flag them in Step 4.

1. Check where you are. It must list your workload and sandbox account ids and `DPDP_TARGET=workload`.
   ```bash
   for p in dpdp-workload-eng dpdp-sandbox-eng; do aws sts get-caller-identity \
     --profile $p --query Account --output text; done; grep DPDP_TARGET config/local.env
   ```
2. Tag both state buckets. It prints one line per bucket.
   ```bash
   T='TagSet=[{Key=Project,Value=dpdp-in-practice},'
   T+='{Key=ManagedBy,Value=bootstrap-script},{Key=DataClass,Value=none}]'
   for p in dpdp-workload-eng dpdp-sandbox-eng; do
     a=$(aws sts get-caller-identity --profile $p --query Account --output text)
     aws s3api put-bucket-tagging --bucket "dpdp-tfstate-$a" --profile $p --tagging "$T"
     echo "Tagged the state bucket of $p"
   done
   ```

---

## Step 3. Bring the model company into line

**Why:** The rules require personal stores to be recoverable. Release 3 adds point-in-time recovery to the four tables and versioning to the two buckets. From this step on, every change goes through `scripts/plan_check.sh` instead of `terraform apply`.

1. Plan and check the change. It must show `Plan: 2 to add, 4 to change, 0 to destroy.` and end with `PASS: the plan meets every rule.`
   ```bash
   scripts/plan_check.sh terraform/live/workload/model-company
   ```
2. Apply it. The script plans and checks again, and applies only the plan it has just checked.
   ```bash
   scripts/plan_check.sh terraform/live/workload/model-company --apply
   ```

The plan check reads the plan as it will be after the change. A compliant change to a non-compliant store therefore passes; a change that leaves anything outside the rules does not.

---

## Step 4. Switch on detection

1. Give the new stack the same state settings as the model company:
   ```bash
   cp terraform/live/workload/model-company/backend.hcl \
     terraform/live/workload/detective/
   ```
2. Allow `PlatformEngineer` to hand AWS Config its role. Turning on the recorder passes that role to AWS Config, which needs `iam:PassRole`; PowerUserAccess excludes it. This adds `iam:PassRole` on the AWS Config role only, nothing else, to the `PlatformEngineer` permission set, in every account where it is assigned. It runs once, as the management administrator, in IAM Identity Center (US East). It must end with `Inline policy added to PlatformEngineer.` and `Provisioning: SUCCEEDED`. If `PlatformEngineer` was given an inline policy of your own, it stops without changing it.
   ```bash
   (
   set -eo pipefail
   P=dpdp-mgmt-admin
   R=us-east-1
   I=$(aws sso-admin list-instances --profile $P --region $R \
     --query 'Instances[0].InstanceArn' --output text)
   PS=""
   for a in $(aws sso-admin list-permission-sets --instance-arn $I --profile $P \
       --region $R --query 'PermissionSets[]' --output text); do
     n=$(aws sso-admin describe-permission-set --instance-arn $I \
       --permission-set-arn $a --profile $P --region $R \
       --query PermissionSet.Name --output text)
     if [ "$n" = "PlatformEngineer" ]; then PS=$a; fi
   done
   [ -n "$PS" ] || { echo "STOP: PlatformEngineer not found"; exit 1; }
   cur=$(aws sso-admin get-inline-policy-for-permission-set --instance-arn $I \
     --permission-set-arn $PS --profile $P --region $R \
     --query InlinePolicy --output text)
   if [ -n "$cur" ] && [ "$cur" != "None" ]; then
     echo "$cur"; echo "STOP: PlatformEngineer already has an inline policy"; exit 1
   fi
   POL='{"Version":"2012-10-17","Statement":[{"Sid":"PassConfigServiceLinkedRole",'
   POL+='"Effect":"Allow","Action":"iam:PassRole","Resource":"arn:aws:iam::*:role/'
   POL+='aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig"}]}'
   aws sso-admin put-inline-policy-to-permission-set --instance-arn $I \
     --permission-set-arn $PS --inline-policy "$POL" --profile $P --region $R
   echo "Inline policy added to PlatformEngineer."
   REQ=$(aws sso-admin provision-permission-set --instance-arn $I \
     --permission-set-arn $PS --target-type ALL_PROVISIONED_ACCOUNTS \
     --profile $P --region $R \
     --query PermissionSetProvisioningStatus.RequestId --output text)
   for i in $(seq 1 30); do
     s=$(aws sso-admin describe-permission-set-provisioning-status --instance-arn $I \
       --provision-permission-set-request-id $REQ --profile $P --region $R \
       --query PermissionSetProvisioningStatus.Status --output text)
     echo "Provisioning: $s"
     [ "$s" = "IN_PROGRESS" ] || break
     sleep 10
   done
   [ "$s" = "SUCCEEDED" ] || { echo "STOP: provisioning did not succeed"; exit 1; }
   )
   ```
3. Create the role AWS Config works with, unless it already exists. It must print `AWSServiceRoleForConfig`.
   ```bash
   aws iam get-role --role-name AWSServiceRoleForConfig --profile dpdp-workload-eng \
     --query Role.RoleName --output text 2>/dev/null \
     || aws iam create-service-linked-role --aws-service-name config.amazonaws.com \
     --profile dpdp-workload-eng --query Role.RoleName --output text
   ```
   This is done with the AWS CLI, not Terraform: Terraform would also tag the role, and `PlatformEngineer` may create service-linked roles but not tag IAM roles.
4. Plan, check and apply. It must show `PASS` and end with `Apply complete! Resources: 14 added`.
   ```bash
   scripts/plan_check.sh terraform/live/workload/detective --apply
   ```
5. Wait ten minutes while AWS Config records the account for the first time, then look at the rules:
   ```bash
   python tools/drift_drill.py --profile dpdp-workload-eng --status
   ```
   Five rules must show `COMPLIANT`. `dpdp-logs-kept-one-year` shows `INSUFFICIENT_DATA` if the account has no log groups, which is correct. If a rule shows `NON_COMPLIANT`, open **AWS Config** → **Rules** in the console (Mumbai region, workload account) and read which resource it names before you continue.
   AWS Config can take longer to record DynamoDB tables than buckets the first time. Until it has, `dpdp-personal-table-recoverable` shows `INSUFFICIENT_DATA`. Run the command again later, and go on to Step 5 only when that rule shows `COMPLIANT`: Step 5 locks the recorder, so any fix to it afterwards needs the guardrail detached first.

---

## Step 5. Protect detection

**Why:** A detective control that an administrator can switch off proves little. The `buckets` guardrail now also stops anyone in the workload account from stopping, deleting or changing the AWS Config recorder, its delivery channel and its rules. It is applied after Step 4, because it also stops Terraform from changing them. The procedure for later changes is in `policies/scp/README.md`.

1. Plan and check the organisation stack. It must show `Plan: 0 to add, 1 to change, 0 to destroy.`, the change being the content of `protect-log-and-evidence-buckets`, and end with `PASS`.
   ```bash
   scripts/plan_check.sh terraform/live/management/organization
   ```
   If the plan shows any other change, stop and find out why before you apply.
2. Apply it:
   ```bash
   scripts/plan_check.sh terraform/live/management/organization --apply
   ```
3. Try to stop the recorder as the workload administrator. It must be refused with `AccessDeniedException` and the words `explicit deny in a service control policy`.
   ```bash
   aws configservice stop-configuration-recorder \
     --configuration-recorder-name dpdp-recorder --profile dpdp-workload-admin
   ```

---

## Step 6. Two fire drills

**Why:** A control is trusted once it has been seen to work. The first drill tries a non-compliant change through the process; the second makes one outside it.

1. **Through the process.** Plan the deliberately non-compliant stack in `tests/fixtures/noncompliant-stack`: an untagged bucket without a public access block, an unregistered personal table without point-in-time recovery, and a log group kept for 7 days. It must list five `FAIL` lines, one each for `[s.8(1)]` (twice), `[R.6(1)(b)]`, `[R.6(1)(d)]` and `[R.6(1)(e)]`, and end with `BLOCKED: the plan breaks the rules above. Nothing was applied.`
   ```bash
   scripts/plan_check.sh tests/fixtures/noncompliant-stack
   ```
2. **Outside the process.** Create an untagged bucket and a 7-day log group by hand, and wait for AWS Config. It takes 2 to 15 minutes and must end with two lines `NON_COMPLIANT after ...`.
   ```bash
   python tools/drift_drill.py --profile dpdp-workload-eng
   ```
3. Remove both:
   ```bash
   python tools/drift_drill.py --profile dpdp-workload-eng --remove
   ```
   For a few minutes after the removal, `--status` can still show `dpdp-store-has-dataclass` and `dpdp-logs-kept-one-year` as `NON_COMPLIANT`, for the two resources just removed. They clear once AWS Config records the removal; the log rule clears at its next evaluation.

The findings stay in AWS Config's history, with the time each change was made and detected: **AWS Config** → **Resources**, then the bucket `dpdp-drift-drill-<workload id>`.

---

## Step 7. Run the tests and check the evidence

Tests T9 to T11 of Release 2 need the planted problems of Release 2, so they are planted for the run and removed after it.

1. Offline tests. They must report `5 passed, 17 skipped`.
   ```bash
   python -m pytest
   ```
2. Plant the Release 2 problems:
   ```bash
   python tools/plant_findings.py --profile dpdp-workload-eng
   ```
3. All tests, including those against AWS. They take 5 to 15 minutes, because T14 waits for AWS Config. They must report `22 passed`.
   ```bash
   python -m pytest --live -v
   ```
4. Remove the Release 2 problems again:
   ```bash
   python tools/plant_findings.py --profile dpdp-workload-eng --remove
   ```

The four new tests:

| Test | Control | Account and role | What it checks | Pass means |
|---|---|---|---|---|
| T12 | DPDP-Act-S8(1), Rule 6(1)(b), (d), (e) | none (offline) | The rules' unit tests, a compliant plan and a non-compliant plan | The compliant plan passes; the non-compliant plan is stopped once for each provision |
| T13 | same | workload, PlatformEngineer | `scripts/plan_check.sh` on the non-compliant stack | Exit code 3 (blocked), every provision named, and nothing created |
| T14 | DPDP-Rule-6(1)(g) | workload, PlatformEngineer | A bucket and a log group made by hand | AWS Config marks both `NON_COMPLIANT` within 15 minutes; both are removed |
| T15 | DPDP-Rule-6(1)(g) | workload, BreakGlassAdmin | Stopping the recorder and deleting a rule | Both refused, and the recorder still recording |

5. Load your settings into the terminal:
   ```bash
   set -a; source config/local.env; set +a
   ```
6. List the evidence records of the new live tests. Three records must be listed, one each for T13, T14 and T15.
   ```bash
   aws s3 ls s3://$DPDP_EVIDENCE_LIVE_BUCKET/dpdp-workload/ --recursive \
     --profile dpdp-logarchive-auditor | grep -E "t13-|t14-|t15-" | tail -3
   ```

---

## Step 8. Optional: check every pull request in GitHub

**Why:** `scripts/plan_check.sh` works when people use it. Checking every pull request in GitHub makes it a gate nobody can skip: a change that breaks a rule cannot be merged. GitHub gets credentials for each run through OpenID Connect, which expire after the run, instead of an access key kept in its settings (Rule 6(1)(b)). The role can read resource settings, but not the contents of buckets, tables or logs.

Do this only in your own copy on GitHub (setup guide, Part 1.4). Without it, the `plan` job is skipped and the other checks still run.

1. Write the repository's name and ids into the stack's settings, from your copy's own address and GitHub's public API. It must print three lines: `github_repository`, `github_owner_id` and `github_repository_id`.
   ```bash
   r=$(git remote get-url origin \
     | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')
   curl -fsS "https://api.github.com/repos/$r" | python3 -c 'import json, sys
   d = json.load(sys.stdin)
   print("github_repository    = \"%s\"" % d["full_name"])
   print("github_owner_id      = \"%s\"" % d["owner"]["id"])
   print("github_repository_id = \"%s\"" % d["id"])' \
     > terraform/live/workload/ci-plan/terraform.tfvars
   cat terraform/live/workload/ci-plan/terraform.tfvars
   ```
   GitHub identifies each pull request's run by the repository's owner and name together with their numeric ids, which never change. The role trusts exactly those, so a deleted name taken over by someone else cannot use it ([GitHub changelog, 23 April 2026](https://github.blog/changelog/2026-04-23-immutable-subject-claims-for-github-actions-oidc-tokens)). Repositories created after 15 July 2026 use this form automatically; for an older copy, switch on immutable subject claims in its OIDC settings first.
2. Give the stack its state settings, with the administrator profile (this stack creates an IAM role, which PlatformEngineer cannot do):
   ```bash
   sed 's/dpdp-workload-eng/dpdp-workload-admin/' \
     terraform/live/workload/model-company/backend.hcl \
     > terraform/live/workload/ci-plan/backend.hcl
   ```
3. Plan, check and apply. It must end with `Apply complete! Resources: 4 added`.
   ```bash
   scripts/plan_check.sh terraform/live/workload/ci-plan --apply
   ```
4. Print the two values for GitHub. They contain your account id: paste them only into GitHub's secrets, nowhere else.
   ```bash
   terraform -chdir=terraform/live/workload/ci-plan output -raw plan_role_arn; echo
   aws sts get-caller-identity --profile dpdp-workload-eng --query Account --output text
   ```
5. **GitHub:** in your copy, **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Create two secrets: `AWS_PLAN_ROLE_ARN` with the first value, and `AWS_ACCOUNT_ID` with the second.
6. Open any pull request. The check **Plan the workload stacks and check them** must pass, with `PASS` or `0 failures` for each of the three stacks. GitHub masks the account id in its logs.

---

## What stays

Nothing needs removing: the fire drills cleaned up after themselves. The detective controls and the guardrail stay, because they are the controls. AWS Config's history bucket keeps the record of every change. To remove the detective controls later, follow `policies/scp/README.md`: detach the `buckets` guardrail from the Workloads unit, destroy the stack, attach the guardrail again.

---

## Beyond the code

The plan check and AWS Config cover infrastructure built in the cloud account. Prevention in a company is mostly a change process, with people deciding what may change and when.

**1. The decisions management takes**

- Every change to systems holding personal data goes through the same process: a pull request, the plan check, a reviewer, and an approver who is not the author.
- Exceptions are allowed, but written down: who approved it, why, and until when. An exception without an expiry date is a new standard.
- Which rules block a change, and which only warn. In this build every rule blocks; a company often starts by warning, measures, then blocks.
- How quickly a flagged change must be dealt with, for example within two working days.

**2. Owners**

| Activity | System owner | DPO | IT and cloud | CISO | Internal audit |
|---|---|---|---|---|---|
| Writing and changing the rules | C | C | R | A | I |
| Approving a change | A | I | R | C | I |
| Approving an exception | A | C | C | C | I |
| Dealing with a flagged change | A | I | R | C | I |
| Independent check that the process is followed | I | I | I | I | A |

A: accountable. R: responsible. C: consulted. I: informed. For exceptions, the system owner decides and the CISO must agree; one person is accountable, as in the operating model's governance charter.

**3. The procedure**

1. Every change starts as a pull request, with a reason.
2. The plan is checked against the rules; a reviewer reads the plan and the result.
3. Changes made outside the process are reviewed weekly from AWS Config: each is either brought into the code, or reversed.
4. The rules themselves change only through the same process, with the DPO consulted.

**4. The evidence**

- The pull request with its plan-check result and approval.
- AWS Config's history: what changed, when, and its compliance at the time.
- The exceptions register.
- The test records of T12 to T15.

**5. Effort** (indicative, for a mid-sized company)

- First version of the rules and the gate: 2 to 4 weeks.
- Each new rule: a day or two, including its tests.
- The ongoing cost is in reviewing flagged changes and exceptions, not in the tooling.

**6. Outside AWS**

The same idea applies wherever personal data is configured: SaaS applications (who can export, sharing settings), databases on premises, and laptops. Many SaaS products offer audit logs and configuration exports that can be checked the same way, on a schedule.

## How a company would run this

| Part | In this release | In a company |
|---|---|---|
| Applying changes | From the laptop, through `scripts/plan_check.sh` | From a pipeline only, after approval; people have no direct write access (a later release) |
| The plan check | Locally, and on pull requests if Step 8 is done | On every pull request, as a required check that cannot be bypassed |
| Detection | AWS Config in one account, three resource types, six rules | An aggregator across all accounts, more resource types, often with a security dashboard on top |
| Response to a flagged change | Read in AWS Config | A ticket for the owner, with a deadline; repeated drift raised in the change review |
| Exceptions | None | A register with owner, reason and expiry, reviewed monthly |

## What Release 3 does not do

- **Changes are still applied from the laptop.** The plan check is a gate on the laptop and, with Step 8, on pull requests. An approval-gated pipeline that removes direct write access comes in a later release.
- **Encryption at rest is not checked.** S3 has encrypted every new object by default since January 2023, and DynamoDB always encrypts its tables, so a rule would always pass. Encryption with customer-managed keys is a later question.
- **AWS Config runs in the workload account only,** for S3 buckets, DynamoDB tables and log groups. The sandbox gets the same controls only during the clean-room test before a release.
- **No automatic correction.** A flagged change is reported, not reversed. Reversing automatically can destroy data or break a service; a person decides.
- **No alerts.** Findings are visible in AWS Config and through `tools/drift_drill.py --status`. Notifications come with breach response.
- **The register link is a tag check in AWS Config.** The plan check confirms that `RegisterStore` names a real register entry; AWS Config confirms only that the tag is present.
- One person holds every role. In a real organisation, the author of a change and its approver are different people.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `STOP: could not download conftest` | The version in `config/tool-versions.env` is not on the conftest releases page. Choose a listed version, change the file, run the script again |
| `conftest is not installed` | Run Step 1, items 3 and 4 |
| `terraform plan failed` with `No valid credential sources` or `Token has expired` | Run `aws sso login --sso-session dpdp` again |
| Step 3 plan shows more than `2 to add, 4 to change` | Something in the account differs from the code. Read the plan; do not apply until you know why |
| Step 4: `no matching IAM Role found` for `AWSServiceRoleForConfig` | Step 4, item 3 was not run in this account. Run it, then repeat item 4 |
| Step 4: `not authorized to perform: iam:PassRole` | Step 4, item 2 was not run, or its provisioning had not finished. Run it, then repeat item 4 |
| Step 4: `MaxNumberOfConfigurationRecordersExceeded` | A recorder already exists in this account and region. Remove it in the AWS Config console, or ask for help in the repository's issues |
| Step 4: a rule stays `NON_COMPLIANT` for a state bucket | Step 2 was not run for that account |
| T14 fails: "not flagged" | AWS Config can be slow to record a new resource. Run `python -m pytest --live tests/prevent/test_t14_drift_detected.py` again |
| T15 skipped | `DPDP_TARGET` is `sandbox`. T15 runs only against the workload account, where the guardrail applies |
| Step 8: `EntityAlreadyExists` for the OpenID Connect provider | The account already trusts GitHub. Import it: `terraform -chdir=terraform/live/workload/ci-plan import aws_iam_openid_connect_provider.github arn:aws:iam::<workload id>:oidc-provider/token.actions.githubusercontent.com`, then repeat Step 8, item 3 |
| Step 8: the `plan` job is skipped | The two secrets are not set, or the pull request comes from a fork. GitHub gives no credentials to pull requests from forks, by design |
