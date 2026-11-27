# AI governance: governing an AI assistant before it is built

**DPDP in Practice · AI governance.** Companion release to Release 4 (`v0.5.1`). No AWS resources.

Fernleaf Finance (fictional) plans a borrower assistant: a chat assistant in its app, built in Release 12 and attacked in Release 13. This release does what should happen before any of that is built. It records the assistant, the model behind it, and the AI tools staff use in an **AI register** that is checked on every pull request; it gives each AI decision one owner; and it assesses the assistant's impact on the people who will use it.

It is written for the people who approve AI in a regulated company: the board of directors, the CEO, the Chief Risk Officer, the CTO, the CISO, the Privacy Lead, General Counsel and Internal Audit.

---

## What applies, and what it asks for

No Indian law is specific to AI. The DPDP Act applies to AI as it applies to any processing, and the sector regulators add their own expectations. This release keeps the binding duties, the draft or voluntary guidance, and the design choices apart.

| Source | Status | What it asks for, as used here |
|---|---|---|
| DPDP Act s.4, s.6(1) | Binding from 13 May 2027 | Personal data only for a lawful purpose, with a recorded basis, and limited to what the purpose needs. An AI system is no exception |
| DPDP Act s.8(1), s.8(2) | Binding from 13 May 2027 | The company answers for all processing, including by an AI system and by the provider of its model, who works under a contract |
| DPDP Act s.8(5); Rule 6(1)(a) to (g) | Binding from 13 May 2027 | Security safeguards: masking, access control, logs kept a year, the ability to keep working, contract clauses, measures that make them effective |
| DPDP Act s.9 | Binding from 13 May 2027 | Children's data only with verifiable parental consent, and no tracking or targeting of children. The assistant does not use children's data at all |
| RBI draft guidance on model risk management | Draft of 24 June 2026; consultation closed 24 July 2026; not final | A model inventory covering AI and third-party models, with owners, developers, validators, approvers, risk tier, intended use and dependencies; risk tiering; independent validation before and after deployment; human oversight and the ability to suspend a model; telling customers they are dealing with AI, and offering a person |
| RBI FREE-AI committee report | Report of August 2025; recommendations | A board-approved AI policy, an inventory of AI uses, governance of data used by AI, an audit framework |
| CERT-In blueprint on AI-assisted attacks | Guidance of 25 May 2026; not binding | Approval policies for AI use, inventories of AI systems and integrations, limits on sensitive data sent to public AI services, access control and logging for AI |
| MeitY India AI Governance Guidelines | November 2025; not binding | Principles such as accountability and "understandable by design"; grievance redressal for people affected by AI |
| ISO/IEC 42001 | Voluntary standard | A management system for AI: policy, roles, impact assessment, life cycle, data, information for users, third parties. Used here as a checklist, not for certification |

| A design choice of this release, recommended but not required |
|---|
| An AI register in the repository, checked by code on every pull request, linked to the personal data register |
| Treating the RBI draft's inventory fields and human-oversight expectations as if final |
| A Chief Risk Officer who validates and approves AI systems, independent of their owner |
| Models run in India only, through an India inference profile |
| An impact assessment for an AI system, although Fernleaf is not a Significant Data Fiduciary |

---

## The files

| File | What it is |
|---|---|
| [`../register/ai-register.yaml`](../register/ai-register.yaml) | The AI register: the borrower assistant, its tools and controls; the model inventory entry; the AI tools staff use |
| [`../tools/ai_register_check.py`](../tools/ai_register_check.py) | The check. It fails when an AI system would use personal data the personal data register does not know, act without the approval decided, log unmasked prompts, or send data outside India |
| [`impact-assessment-borrower-assistant.md`](impact-assessment-borrower-assistant.md) | The impact assessment of the assistant, following the template of the operating model, with sections on what it may do and how it is stopped |
| [`decisions.md`](decisions.md) | The ten decisions to take before the build: five decided, five open. Each with one decider |
| [`ai-use-policy.md`](ai-use-policy.md) | The policy on the use of AI, for staff and for AI systems |
| [`../operating-model/raci.xlsx`](../operating-model/raci.xlsx), sheet `AI` | One row for each AI activity, with one accountable role per row, checked by a formula |
| [`../operating-model/governance-charter.md`](../operating-model/governance-charter.md) | The Chief Risk Officer's role, and the decision rights for AI |
| [`../operating-model/board-report-template.md`](../operating-model/board-report-template.md), section 8 | What the board sees about AI each quarter |

---

## Run the check

```bash
python tools/ai_register_check.py
```

Expected result: `Result: PASS (0 failures, 4 open items)`. The four open items are real: the legal basis (D-3), the new category for conversations (D-4), the provider as a Data Processor (D-5), and validation, which can only happen once something is built. An open item is allowed only while the assistant is `planned`: if its status changes to `in_development` while the purpose or the category is still missing from the personal data register, the check fails.

Two tests run it, with no AWS access:

| Test | What it attempts | Pass means |
|---|---|---|
| T21 | Checks the AI register against the personal data register | No failures |
| T22 | Six broken copies of the AI register: a model through a profile that can leave India; a tool that changes a loan with no rule on anyone's approval; a tool that reads credit bureau data the assistant does not list; model invocation logging switched on; the owner validating their own system; the assistant moved into development while its purpose is still missing from the personal data register | Each copy fails with the provision it breaks |

---

## How to adopt it, in order

1. **List what exists.** Every AI system the company runs, every model behind one, and every AI tool staff use, including AI features switched on inside existing products. Release 2's approach of not trusting a single list applies here too: invoices and expense claims show the paid tools, and sign-in records and web proxy logs show many of the free ones.
2. **Name the owners.** One accountable role for each AI system and each staff AI tool; a validator independent of the owner.
3. **Write the rules down as data.** For each AI system: the personal data it may use, the tools it may call, which actions a person approves, and who can suspend it.
4. **Check it on every change.** The AI register is checked like the personal data register, before every commit and on every pull request.
5. **Assess before building.** An impact assessment and a validation plan, approved before the build starts.
6. **Take the open decisions.** Each with its decider, recorded.
7. **Have it checked.** Internal Audit checks, within the first year, that the AI register matches what is running.

---

## How it connects to the rest of this project

| Where | What this release adds |
|---|---|
| The personal data register (Release 1) | Every category and purpose an AI system uses must be in it. The check fails otherwise |
| Discovery (Release 2) | The same method finds the AI tools staff use without approval |
| Prevent (Release 3) | The assistant's stores will carry register tags, so the plan check stops one that is not registered. Its policy and guardrail settings will be checked the same way in Release 12 |
| The operating model | The RACI gains an `AI` sheet; the charter gains the Chief Risk Officer and the AI decisions; the policy index gains policy 19; the quarterly board report covers AI systems in section 8 |
| Notice and consent (Release 4) | If decision D-3 makes the assistant a new purpose, the notice gains a choice, and its version changes |
| Releases 12 and 13 | The assistant is built against this register, and attacked against the risks in the impact assessment |

---

## Beyond the documents

**1. The decision management takes.** The board of directors approves the policy on the use of AI and appoints the Chief Risk Officer as the validator of AI systems. Without that, the AI register is a list, not a control.

**2. Owners.**

| Activity | Board of directors | CEO | CTO | Chief Risk Officer | Internal Audit |
|---|---|---|---|---|---|
| Approving the policy on the use of AI | A | R | R | C | I |
| Keeping the AI register accurate | I | I | A | C | I |
| Validating an AI system before deployment | I | I | C | A | I |
| Independent check that the register matches what runs | I | I | I | I | A |

**3. The procedure.** A new AI system or staff AI tool enters the AI register before anything is built or bought; the check passes; the impact assessment is approved; the open decisions are closed; the Chief Risk Officer validates before deployment; the privacy committee sees every change; the board sees the AI register's status in the quarterly report.

**4. The evidence.** The AI register's history in Git; the check's results on every pull request; the signed impact assessment; the decision log; the validation reports; the quarterly report.

**5. Effort** (indicative, for a mid-sized company). Two to four weeks to list what exists and agree the owners. The first AI system's register entry and impact assessment: one to two weeks. Each later system: a few days.

**6. Beyond AWS.** The register, the owners and the decisions apply whatever the platform or model. Only the controls in an entry's `controls` section are specific to Amazon Bedrock.

---

## What this release does not do

- **It builds nothing in AWS.** The assistant is built in Release 12 and attacked in Release 13.
- **It does not take the open decisions.** D-3, D-4, D-5, D-7 and D-10 need people, and the check keeps them visible until they are taken.
- **The RBI guidance is a draft.** It is used as if final; when RBI issues the final version, the inventory fields and this release are checked against it.
- **It is not legal advice.** The legal basis for the assistant (D-3) in particular is for counsel.
- **One person holds every role.** In a real organisation, the validator is independent of the people who build.

---

Not legal advice.
