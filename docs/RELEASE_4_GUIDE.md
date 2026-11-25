# DPDP in Practice: Release 4 Guide

**Release 4: Notice and consent.**

Edition for Release 4 (`v0.5.0`). Start this guide only when the **Release 3 Guide** is complete: the model company in your workload account with its synthetic customers, the plan check installed, AWS Config running, and the Release 3 tests passing. The commands follow the same layout as the other guides: one command per grey box, numbered in order, and a backslash `\` where a command continues on the next line. Account ids are read from your AWS sign-in; you never type one.

Releases 1 to 3 recorded what Fernleaf Finance (fictional) holds and kept it safe. Release 4 deals with the moment a person is asked for her consent:

- **The notice is written by people and checked against the register.** The Privacy Lead writes the wording and General Counsel approves it. The data each purpose uses, what it makes possible and who receives the data are taken from the register, in English and Hindi. A notice that leaves out a purpose the company records, or offers one it does not, cannot be published.
- **Consent is checked before it is recorded.** A consent service, reachable only with a signed request, refuses a consent the app reports as ticked in advance, several purposes bundled into one choice, data the purpose does not need, a purpose processed under Section 7, and a notice that is not the current one. Each refusal names its provision. The service checks what the app reports; it cannot see the person's screen, so people review every consent screen before release (see "What the service can and cannot know" in Step 5).
- **Every consent can be proved.** Each accepted consent is kept twice: as a locked copy that nobody can change or delete for a year, and as a row in a ledger that points to it. A change to the ledger is found by comparing it with the locked copy.
- **Earlier customers get the notice.** Customers who consented before the notice existed are given it, and the company can show who has received it.

Start every working session with these two commands:

```bash
cd ~/work/dpdp-on-aws && source .venv/bin/activate
```
```bash
aws sso login --sso-session dpdp
```

## What Release 4 proves

| DPDP provision | What the system does | Test |
|---|---|---|
| Section 5(1), with Section 5(3), Section 6(3) and Rule 3 | The notice is complete on its own: itemised data, each purpose, what it enables, the links to withdraw consent, exercise rights and complain to the Board, and the contact, in English and Hindi. A consent can only cite the current notice | T16, T17 |
| Section 6(1) | Only consent that is specific, by a clear affirmative action, informed by the notice, and limited to the data the purpose needs is recorded; anything else is refused, whole | T17, T18 |
| Section 6(10) | The company can prove each consent from a locked copy nobody can change; producing the proof needs only read-only access, a change to the ledger is found, and the locked copy cannot be deleted | T19 |
| Section 5(2) | Every customer who consented before the notice existed is given it, and the company can show who has been | T20 |
| Rule 6(1)(b), (c) | The consent service accepts signed requests only, and every request is in an access log kept for a year, with the same reference as the record it made | T18 |

Rule 3 of the DPDP Rules sets what the notice contains: it must be understandable on its own (3(a)); give an itemised description of the personal data and the specified purposes, with the goods or services they enable (3(b)); and give the link through which the person can withdraw consent as easily as she gave it, exercise her rights and complain to the Data Protection Board (3(c)). Section 6(3) adds the contact details of the person who answers her questions.

## How it works

```
 app (here: tools/consent_client.py, signed as PlatformEngineer)
   |  GET /notice            POST /consents          POST /notice-deliveries
   v
 API Gateway (HTTP API): signed requests only; access log kept 365 days
   v
 Lambda: services/consent  -- checks each request against the current notice
   |                        (consent_rules.py); accepts it whole or refuses it whole
   +--> dpdp-notices-<id>          notice versions (locked), read only
   +--> dpdp-consent-records-<id>  one locked copy per record (Object Lock)
   +--> dpdp-consent-ledger        one row per record: where its locked copy is,
                                   and its SHA-256 fingerprint
```

| Part | Where | What it does |
|---|---|---|
| Notice | `tools/notice.py`, with `register/personal-data-register.yaml` | Puts the approved wording together with the register's data, purposes and recipients, in English and Hindi; checks the result against Rule 3 and the register; publishes it only if the check passes. The version name comes from the notice's own fingerprint (`N-` and 12 characters), so a version always means one exact text |
| Consent rules | `services/consent/consent_rules.py` | The checks of Sections 5(1), 6(1) and 6(3), and the shape of each record. No AWS calls |
| Consent service | `services/consent/handler.py`, deployed by `terraform/modules/consent-service` | Three routes, each requiring a signed request. Its role can read notices and add records, never change or delete them |
| Proof | `tools/consent_proof.py` | For one customer, checks each record against its locked copy and the notice it cites. Read-only |
| Fire drill | `tools/consent_drill.py` | Changes a consent in the ledger, shows the proof catching it, puts it back, and tries to delete the locked copy |
| Earlier customers | `tools/old_consents.py` | The Section 5(2) campaign: who must receive the notice, who has, who is still waiting |

The locked copies are what make the proof hold. The ledger is an ordinary table that engineers can write to; if anyone changes a row, it no longer matches its locked copy, and the proof says so. In the workload account the copies are locked in compliance mode: nobody, including the root user, can change or delete them for 365 days.

## What Release 4 adds

| Item | Value |
|---|---|
| New stacks | `terraform/live/workload/consent` and `terraform/live/sandbox/consent`, from the module `terraform/modules/consent-service`: two locked buckets, one table, one function with its role, one HTTP API, two log groups (27 resources) |
| Function code | `services/consent/handler.py` and `consent_rules.py` (Python 3.12, on AWS Lambda) |
| Tools | `tools/notice.py`, `tools/consent_client.py`, `tools/consent_proof.py`, `tools/consent_drill.py`, `tools/old_consents.py` |
| Register | A fixed id for each purpose; the Hindi text; what each purpose enables; the notice's contact and links; two new stores and the category "Notice and consent records" |
| Plan-check rule | `[R.6(1)(b)]`: every API route requires authorisation (`policies/rego/prevent.rego`, with unit tests) |
| Tests | T16 and T17 offline, T18 to T20 live; 27 in total: 7 offline, 20 live. T4 now also accepts the consent records in the customer summary |
| Who applies the stack | `BreakGlassAdmin` (`dpdp-workload-admin`): the stack creates an IAM role for the function, which `PlatformEngineer` cannot do, by design |
| New settings | None. The tools find the API and the buckets from your account |
| Cost | A few cents a month at this size: Lambda, API Gateway and DynamoDB are charged per request; the buckets and logs hold a few megabytes |

---

## Step 1. Take Release 4

1. Bring the new code into your copy. If you made your own copy on GitHub (setup guide, Part 1.4), use `git pull upstream main` instead.
   ```bash
   git pull
   ```
2. Install the Python packages, in case they changed:
   ```bash
   pip install -r requirements.txt
   ```
3. Check the register. It must end with `Result: PASS (0 failures, 7 warnings to review)`. The seventh warning is new: the retention period of the consent records is not yet confirmed.
   ```bash
   python tools/register_check.py | tail -1
   ```
4. Run the offline tests. They must report `7 passed, 20 skipped`.
   ```bash
   python -m pytest
   ```

---

## Step 2. Read the notice

**Why:** The notice is the first thing the person sees, and Section 6(1) makes consent valid only if it is informed. Its lists come from the register and its wording from people, so read it as a customer would, in both languages.

1. Check it. It must print the version, `8 choices, 1 purpose under Section 7, languages en, hi`, and `Result: PASS`.
   ```bash
   python tools/notice.py check
   ```
2. Read it in English:
   ```bash
   python tools/notice.py show --language en
   ```
3. Read it in Hindi:
   ```bash
   python tools/notice.py show --language hi
   ```

Each of the eight purposes is a separate choice, numbered, with three lines: the data it uses, what it enables, and who receives the data. Complaints handling is listed apart, because Fernleaf processes it under Section 7(a), not on consent: asking for consent to it would mislead. The teen wallet is not in this notice; a parent's notice and consent come in Release 6.

To change the notice, change the register, not the notice: the next `check` gives a new version name, and the next `publish` (Step 4) makes it current.

---

## Step 3. Deploy the consent service

**Why:** The service is where the rules of Section 6(1) are applied to every request. It creates an IAM role for its function, so this stack is applied as `BreakGlassAdmin`, like the pull request role of Release 3.

1. Give the stack its state settings, with the administrator profile:
   ```bash
   sed 's/dpdp-workload-eng/dpdp-workload-admin/' \
     terraform/live/workload/model-company/backend.hcl \
     > terraform/live/workload/consent/backend.hcl
   ```
2. Plan and check. It must show `Plan: 27 to add, 0 to change, 0 to destroy.` and end with `PASS: the plan meets every rule.`
   ```bash
   scripts/plan_check.sh terraform/live/workload/consent
   ```
3. Apply it. It must end with `Apply complete! Resources: 27 added, 0 changed, 0 destroyed.` and print four outputs: `api_endpoint`, `ledger_table`, `notices_bucket` and `records_bucket`.
   ```bash
   scripts/plan_check.sh terraform/live/workload/consent --apply
   ```

The two buckets are created with Object Lock in compliance mode. From the moment the first notice or consent is written, they cannot be removed for 365 days. That is the point of them; it is also why nothing in this release is removed afterwards (see "What stays").

---

## Step 4. Publish the notice

**Why:** A consent must cite the notice the person was shown, and only the current one is accepted. Publishing writes the notice into the locked notices bucket and makes it current.

1. Publish. It must print `Notice N-... published and made current.`
   ```bash
   python tools/notice.py publish --profile dpdp-workload-eng
   ```
2. Run it again. It must print `... is already the current notice. Nothing changed.`: a version is written once, and stays as it was.
   ```bash
   python tools/notice.py publish --profile dpdp-workload-eng
   ```

---

## Step 5. Give consent, and see what is refused

**Why:** A control is trusted once it has been seen to refuse what it should. Here `tools/consent_client.py` plays Fernleaf's app: it reads the notice from the API, then sends the consent, signed with your engineer profile.

**What the service can and cannot know.** The consent service never sees the customer's screen. It knows only what the app sends with each consent, and one of those values is how the box came to be ticked:

- `customer_ticked`: the box was empty when the screen opened, and the customer tapped it;
- `pre_ticked`: the box was already ticked when the screen opened.

The app knows which, because it drew the screen and saw the tap. The service records the first and refuses the second.

This catches a screen that has been set up, or later changed, to tick a box by default, as long as the app reports it as it is. It does not catch an app that sends `customer_ticked` for a box the customer never touched, whether through a coding error or on purpose: the service would believe it. That gap is closed by people and by tests of the app, not by the service. Every consent screen is reviewed before release, and the app's own tests show that it reports each box truthfully ("Beyond the code", the procedure, items 3 and 4).

1. Read the notice through the API, as the app would before asking. It prints the version, its fingerprint and the eight choices, then the text.
   ```bash
   python tools/consent_client.py notice --profile dpdp-workload-eng | head -12
   ```
2. A box the app reports as ticked in advance (`--pre-ticked` makes the stand-in app send `pre_ticked`). It must print `HTTP 400` and `REFUSED [s.6(1)] ... the action was 'pre_ticked'`, then `Nothing was recorded.`
   ```bash
   python tools/consent_client.py give --customer C-TEST-0001 \
     --purpose marketing-offers --pre-ticked --profile dpdp-workload-eng
   ```
3. Data the purpose does not need: the Aadhaar number for marketing offers. It must print `HTTP 400` and `REFUSED [s.6(1)] Purpose 'marketing-offers' does not need aadhaar_number`.
   ```bash
   python tools/consent_client.py give --customer C-TEST-0001 \
     --purpose marketing-offers --extra-field aadhaar_number --profile dpdp-workload-eng
   ```
4. Two purposes bundled into one choice. It must print `HTTP 400` and `REFUSED [s.6(1)] Choice 1 bundles several purposes`.
   ```bash
   python tools/consent_client.py give --customer C-TEST-0001 \
     --purpose marketing-offers --purpose fraud-detection --bundled \
     --profile dpdp-workload-eng
   ```
5. A request nobody signed. It must print `HTTP 403` and `Forbidden`: API Gateway refuses it before it reaches the service.
   ```bash
   python tools/consent_client.py give --customer C-TEST-0001 \
     --purpose marketing-offers --unsigned --profile dpdp-workload-eng
   ```
6. A valid consent: two purposes, each ticked by the customer. It must print `HTTP 201` and two `RECORDED` lines, each with its locked copy under `consents/C-TEST-0001/`.
   ```bash
   python tools/consent_client.py give --customer C-TEST-0001 \
     --purpose marketing-offers --purpose fraud-detection --profile dpdp-workload-eng
   ```

Every refusal starts with its provision, as the plan check of Release 3 does. A request with one good choice and one bad one is refused whole: nothing from it is recorded.

---

## Step 6. Prove the consent, and try to change it

**Why:** Section 6(10) puts the burden of proof on the company: it must be able to prove that each consent was given, and given properly. Here the company produces that proof with the `Auditor` profile, which can read and change nothing, so producing the proof can never alter a record. Anyone who checks the proof, an internal auditor or the Data Protection Board, can be given the same read-only access.

1. Prove the consents of the test customer. Each record must show `VERIFIED`, the notice version, `by customer_ticked through app`, and `locked (COMPLIANCE) until` a date one year ahead. It must end with `Result: VERIFIED`.
   ```bash
   python tools/consent_proof.py --customer C-TEST-0001 --profile dpdp-workload-auditor
   ```
2. The fire drill: change the newest consent's purpose in the ledger, as someone with write access could, then put it back. It must show `Proof: ALTERED` with the two purposes, then `Ledger put back. Proof: VERIFIED`, then `Delete locked copy: refused, AccessDenied`, and end with `Result: PASS, the change was caught and the proof holds`.
   ```bash
   python tools/consent_drill.py --customer C-TEST-0001 --profile dpdp-workload-eng \
     --auditor-profile dpdp-workload-auditor
   ```

The proof reports the purpose, time and manner from the locked copy, never from the ledger. A change to the ledger therefore shows up as a difference; it cannot replace what was recorded.

---

## Step 7. Give the notice to earlier customers

**Why:** Section 5(2): a person who consented before the Act's obligations began must be given the notice as soon as reasonably practicable. Processing may continue until she withdraws. The company must be able to show who has received it.

1. The report. It counts the open adult accounts (about 160 with the default synthetic data), the ones already covered (`C-TEST-0001`, who consented in Step 5 against the current notice), the ones still waiting, and those left out: closed accounts, whose data Fernleaf keeps because other laws require it, not on the basis of consent (the model company's reading; a company confirms its own with counsel); and teen accounts, whose notice goes to the parent in Release 6.
   ```bash
   python tools/old_consents.py --profile dpdp-workload-eng
   ```
2. Record the deliveries. It takes about a minute, one signed request per customer. The line `Deliveries recorded in this run` must show the number that was waiting, and the line `Still waiting` must show `0`. No message is sent to anyone: the customers are synthetic, and this build has no messaging vendor. In a company, the messaging system would make the same request once each message is delivered.
   ```bash
   python tools/old_consents.py --profile dpdp-workload-eng --send
   ```

---

## Step 8. Run the tests and check the evidence

Tests T9 to T11 of Release 2 need the planted problems of Release 2, so they are planted for the run and removed after it.

1. Offline tests. They must report `7 passed, 20 skipped`.
   ```bash
   python -m pytest
   ```
2. Plant the Release 2 problems:
   ```bash
   python tools/plant_findings.py --profile dpdp-workload-eng
   ```
3. All tests, including those against AWS. They take 5 to 20 minutes: T14 waits for AWS Config, and T18 waits up to three minutes for the API's access log. They must report `27 passed`.
   ```bash
   python -m pytest --live -v
   ```
4. Remove the Release 2 problems again:
   ```bash
   python tools/plant_findings.py --profile dpdp-workload-eng --remove
   ```

The five new tests:

| Test | Control | Account and role | What it checks | Pass means |
|---|---|---|---|---|
| T16 | DPDP-Act-S5(1) | none (offline) | The notice checked against Rule 3 and the register, then two broken copies | Complete in both languages; a missing Hindi text and a missing withdrawal link are both caught |
| T17 | DPDP-Act-S6(1) | none (offline) | The service's own code, with one valid and ten invalid requests | The valid one recorded with matching fingerprints; each invalid one refused with its provision, and nothing recorded |
| T18 | DPDP-Act-S6(1), Rule 6(1)(b), (c) | workload, PlatformEngineer | An unsigned request, a pre-ticked consent and a valid one, through the API | 403, 400, 201; the locked copy in compliance mode, the ledger row, and the access log line with the same request reference |
| T19 | DPDP-Act-S6(10) | workload, PlatformEngineer and Auditor | A new consent, proved; its ledger row changed and put back; its locked copy deleted | VERIFIED, then ALTERED naming the purpose, then VERIFIED; the delete refused |
| T20 | DPDP-Act-S5(2) | workload, PlatformEngineer | The Section 5(2) campaign, then its report | Nobody waiting; closed and teen accounts left out and counted |

5. Load your settings into the terminal:
   ```bash
   set -a; source config/local.env; set +a
   ```
6. List today's evidence records of the new live tests. At least one record must be listed for each of T18, T19 and T20; more than one means the tests ran more than once today.
   ```bash
   aws s3 ls "s3://$DPDP_EVIDENCE_LIVE_BUCKET/dpdp-workload/$(date +%Y-%m-%d)/" \
     --recursive --profile dpdp-logarchive-auditor | grep -E "t18-|t19-|t20-"
   ```

---

## What stays

Everything stays. The consent service is the control, and its records are the proof:

- The notices and consent records are locked for 365 days from when each was written, in compliance mode. Neither bucket can be removed while it holds a locked object. Each test run adds a few records for `C-TEST-0001`; all are synthetic.
- The ledger has deletion protection and point-in-time recovery.
- To remove the service once the last record's lock has expired: set `allow_removal = true` in `terraform/live/workload/consent/main.tf` and apply it through the plan check, which switches off the table's deletion protection and lets Terraform empty the buckets; then run `terraform destroy` in that folder. Until then, its cost is a few cents a month.

---

## Beyond the code

The code checks what can be checked in a request: what the app reports. Whether a consent screen is honest, and whether the app reports it truthfully, is decided by people and by tests of the app, before the screen is released.

**1. The decisions management takes**

- The notice text and each language version: the Privacy Lead writes it, General Counsel must agree (governance charter, section 5). In this build the wording sits in `tools/notice.py` and in the register's `purpose`, `enables` and `*_hi` fields; what is approved is the notice a customer will read (`tools/notice.py show`), not those entries one by one.
- The legal basis of each purpose, and in particular which purposes are not asked for, because they rest on a clause of Section 7.
- How the record of consent is itself justified. Fernleaf treats it as part of each consent: it is described in the notice and is not a separate choice. That is a recorded decision for General Counsel, not a given.
- How long consent records are kept: at least as long as the processing that relies on them, and long enough to answer a proceeding.
- Which languages are offered, and how a person asks for another language of the Eighth Schedule.
- When the Section 5(2) campaign runs, through which channels, and what happens to customers it cannot reach.

**2. Owners**

| Activity | Privacy Lead | General Counsel | CTO | Business owner | Internal audit |
|---|---|---|---|---|---|
| Notice content and language versions | A | C | R | R | I |
| Consent journeys: no pre-ticked boxes, one choice per purpose, data limited | A | C | R | R | I |
| Proof of notice and consent, and replies that rely on it | A | C | R | I | I |
| The Section 5(2) campaign | A | C | R | R | I |
| Independent check of the journeys and the proof | I | I | I | I | A |

A: accountable. R: responsible. C: consulted. I: informed. As in the operating model's RACI, the Privacy Lead is accountable for notice and consent (rows `DPDP-Act-S5(1)`, `S5(2)`, `S6(1)` and `S6(10)`).

**3. The procedure**

1. A new purpose, or a change to one, starts in the register, approved as the governance charter requires.
2. The notice is rebuilt, checked and reviewed in every language before it is published.
3. Every consent screen is reviewed against the notice before release: wording, no box ticked in advance, a separate choice for each purpose, nothing requested that the purpose does not need, and no service refused to a person who declines a purpose the service does not need. Consent must be free and unconditional (Section 6(1)); only a review of the journey can show that.
4. The app's tests show that it reports each box truthfully, and they run on every change to a consent screen. At least two: open the screen, submit without tapping the box, and check that the app sends no consent for that purpose; open it, tap the box, submit, and check that it sends `customer_ticked`. If a box can ever be shown ticked, a third test checks that the app then sends `pre_ticked`. The service's refusal is the last line of defence; these tests and the review in item 3 are the first.
5. Consent records are checked monthly: a sample of customers is proved end to end, as in Step 6. The sample includes the consent screens in use that month: a reviewer compares each screen with its approved review record.
6. Earlier customers are tracked until none is waiting.

**4. The evidence**

- Every published notice version, locked, with its fingerprint.
- The review record of each consent screen, with screenshots, and who approved it.
- The results of the app's consent-screen tests for each release of the app.
- The ledger, the locked copies, and the proof for any customer on request.
- The Section 5(2) campaign report.
- The test records of T16 to T20.

**5. Effort** (indicative, for a mid-sized company)

- Writing the notice, checking it against an existing register, and its translations: 2 to 4 weeks.
- A consent service and its records: 4 to 8 weeks, depending on how many apps and channels must use it.
- Reviewing consent screens: a few days per journey, repeated at every change.

**6. Outside AWS**

Consent is also collected at branches, by call centres, on paper forms and in partners' apps. Each channel needs the same three things: the current notice shown first, a separate choice for each purpose, and a record that reaches the same ledger. A paper form is scanned and recorded with its form version, as a notice version is here. CRM and marketing tools must read consent from the ledger, not keep their own copy of it. A registered Consent Manager is the subject of Release 6.

**7. When the company adds an AI assistant**

Fernleaf Finance (fictional) plans a chat assistant for borrowers. Its governance comes first, in a companion release straight after this one; the assistant is built in Release 12 and attacked in Release 13. The notice and consent built here are what it will rest on, and the same rules apply to it:

- **The chat is personal data.** What a borrower types, and what the assistant answers about her loan, is a new category in the register, with its stores, purpose, legal basis and retention. The notice then lists it like any other category; nothing about the assistant is added to the notice before it exists.
- **Improving the AI is a separate purpose.** Using chats to test or improve the assistant is not the same purpose as answering the borrower. It is a separate choice, never bundled with the service. The consent service already refuses bundled purposes (T17); the same check applies.
- **The person is told she is talking to an AI**, in the chat itself, and the notice names any model provider that receives the chat, as it names every other recipient.
- **The chat stays in India.** The assistant's model is called through Amazon Bedrock's India-only route, which runs each request in Mumbai or Hyderabad. Routes that can send a chat to other countries are not used.
- **The assistant checks consent before it uses data.** Each tool the assistant can call reads the person's consent first, as any other system must. That check comes with withdrawal, in Release 5.
- **Its records are kept like any other.** The assistant's memory and logs follow the retention, masking and erasure rules of Releases 7 and 8, and a person's request for her data (Release 10) includes her chats.

## How a company would run this

| Part | In this release | In a company |
|---|---|---|
| The app | `tools/consent_client.py`, signed as PlatformEngineer | The app's back end, with its own role, after it has authenticated the customer |
| Who can call the API | Anyone in the account with `execute-api:Invoke` (PlatformEngineer and administrators) | Only the app's back-end roles: `execute-api:Invoke` on this API is allowed to them and denied to everyone else, for example by a guardrail |
| The ledger | Writable by engineers; changes are found by the proof | Writes allowed only to the service's role, through a resource policy on the table; changes refused as well as found |
| Notice publication | `tools/notice.py publish` from the laptop | From the pipeline, after the Privacy Lead's approval |
| Section 5(2) | Deliveries recorded; no message sent | The messaging vendor sends; delivery receipts are recorded; failures are retried or sent another way |
| Languages | English and Hindi | The languages the company's customers use, and any other on request |

## What Release 4 does not do

- **No real app or consent screen, and the service cannot see one.** The service records how consent was given (`customer_ticked`) as the app reports it, and refuses `pre_ticked`. An app that reports `customer_ticked` for a box the customer never tapped would not be caught by the service. Whether the box was really empty, and whether the app reports it truthfully, is shown by reviewing the screen and testing the app ("Beyond the code", the procedure, items 3 and 4).
- **No withdrawal yet.** Withdrawal as easy as consenting, and stopping the processing and the vendors, is Release 5. The notice already gives the link.
- **No children's accounts.** Verifiable parental consent and the parent's notice are Release 6.
- **Two languages.** Adding a language is a change to the register and to the wording table in `tools/notice.py`; Section 5(3) gives the person the choice of any language of the Eighth Schedule.
- **Anyone in the account who may call the API can record a consent for any customer number.** The service checks the consent, not who the customer is: in this build the engineer profile plays the app. A company lets only the app's back end call the API, after the app has signed the customer in.
- **The ledger can be changed by engineers.** Such a change is found by the proof, not prevented. The locked copies cannot be changed by anyone.
- **The retention period of the consent records is not confirmed** (register warning). The lock of 365 days is a minimum, not a deletion date.
- **The access log names the person who signed each request** (the role and the sign-in name). That is staff data, kept for a year for Rule 6(1)(c); a company decides who may read it.
- **AWS Config does not check API routes.** The rule that every route requires authorisation is applied by the plan check only.
- The links in the notice use the reserved domain `fernleaf.example`. A company gives its own, including the way to complain to the Data Protection Board.
- One person holds every role. In a real organisation, the notice text is approved by someone other than its author.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `notice.py check` reports `[Rule 3(b)(ii)] Purpose ... has no purpose text in 'hi'` | A purpose in the register has no Hindi text. Add `purpose_hi` (and `enables_hi`) next to the English text |
| Step 3 plan: `No valid credential sources` or `Token has expired` | Run `aws sso login --sso-session dpdp` again. Administrator sessions last one hour |
| Step 3 plan: `AccessDenied` on `iam:CreateRole` | `backend.hcl` names `dpdp-workload-eng`. Repeat Step 3, item 1, which writes `dpdp-workload-admin` |
| Step 3 plan shows `BLOCKED` | Read the `FAIL` lines: each names its provision and resource. Do not apply until you know why |
| `No API named dpdp-consent-api in this account` | Step 3 was not applied in this account, or the profile points to another account |
| `HTTP 500` and `The record was not made` | Usually the notice is not published: run Step 4. Otherwise read the function's log: **CloudWatch** → **Log groups** → `/aws/lambda/dpdp-consent-api`, and find the request reference |
| `HTTP 400 ... is not the current notice` on a valid consent | The register changed after Step 4. Run Step 2 and Step 4 again |
| `consent_proof.py` shows `NO RECORDS` | No consent recorded for that customer yet. Run Step 5, item 6 |
| `consent_proof.py` shows `ALTERED` outside the drill | A ledger row no longer matches its locked copy. The locked copy is what was recorded. Find who changed the row in CloudTrail (`UpdateItem` on `dpdp-consent-ledger`) |
| T18 fails: `access log line False` | The access log arrived late. Run `python -m pytest --live tests/consent/test_t18_consent_api.py` again |
| `old_consents.py` ends with `FAILED for: ...` | Some deliveries were refused or throttled. Run it again with `--send`: customers already covered are skipped |
