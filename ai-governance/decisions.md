# Decisions to take before the assistant is built

Fernleaf Finance (fictional). Each decision has one decider, following the decision rights in `operating-model/governance-charter.md` (section 5, including the rows added for AI). "Must agree" means the decision cannot be taken without that role's written agreement. Each is recorded in the privacy committee minutes, and where shown, in the AI register.

Status on publication: five decided, five open. The AI register's open items (WARN lines from `tools/ai_register_check.py`) point to the open decisions by number.

| # | Decision | Decides | Must agree | Status | What was decided, or what is needed |
|---|---|---|---|---|---|
| D-1 | Which model, and in which account it runs | CTO | CISO | Decided, to confirm at build | Claude through Amazon Bedrock's India inference profile (routes only between Mumbai and Hyderabad). In the same workload account as the personal data stores, with its own role, tagged resources and a kill switch aimed at that role. Accepted limitation: weaker separation than a separate account. At build: confirm that AgentCore Policy is available in Mumbai, since AWS's region list and its launch notice disagree; if not, tool rules are enforced in the tool code and the IAM role |
| D-2 | A change to the Mumbai-only guardrail for model calls | CISO | CTO | Decided, to confirm at build | A permanent, narrow change to the guardrail, not a 90-day exception: it allows only calls through the India profile (the `bedrock:InferenceProfileArn` condition AWS documents). Everything else stays Mumbai-only, and T6 must still pass. At build: check whether Hyderabad must be enabled for the account |
| D-3 | The legal basis for the assistant's use of loan and repayment data | General Counsel and Company Secretary | Privacy Lead | **Open** | Either within the existing purposes (`loan-collections`, `complaint-handling`), or a new purpose with its own notice choice and basis. Needed before Release 12 |
| D-4 | Conversations as a new category of personal data: store, retention period and its legal reason | Privacy Lead | General Counsel and Company Secretary | **Open** | Entry in the personal data register, with a store tagged for the register (Release 1) and a retention period of at least one year for the logs of processing (Rule 8(3)) |
| D-5 | AWS as a Data Processor for the model service | Business owner (Head of Customer Service) | Privacy Lead and CISO | **Open** | Vendor entry and contract clause in the personal data register (Section 8(2), Rule 6(1)(f)). The provider's terms confirmed in writing: no training on prompts; what is stored for abuse detection, where and for how long |
| D-6 | What the assistant may do: allowed and forbidden tools, and which changes a person approves | Business owner (Head of Customer Service) | Chief Risk Officer and Privacy Lead | Decided, draft | As in the AI register: five tools allowed, two forbidden; a collections officer approves every repayment date change |
| D-7 | Which AI tool staff may use with personal data | CTO | CISO and Privacy Lead | **Open** | One workplace assistant under an enterprise contract: data in India, not used for training, retention set by Fernleaf. Until chosen, no AI tool is approved for personal data |
| D-8 | The assistant's risk tier, and the validation plan before deployment | Chief Risk Officer | (none) | Decided | Tier: high. Independent validation before deployment and after every change to the model, the tools or the prompts. Plan: the Release 13 attack tests, plus a weekly sample of replies once live |
| D-9 | Who may suspend the assistant, and who may restart it | CISO | (none: speed matters) | Decided | The CISO decides; the business owner may also trigger it. Two levels: read-only and halt. Restart needs the Chief Risk Officer |
| D-10 | Replies in Hindi | Privacy Lead | CISO | **Open** | Bedrock Guardrails' Hindi support is on its Standard tier, which uses cross-region processing. Before Hindi is offered, confirm where that processing happens. Until then, the assistant answers in English and offers a person for Hindi |

## Left out, by decision

| Not done | Why |
|---|---|
| Explaining the model's internal workings | Explanations are given at the level of decisions: which tool was called, which policy allowed it, who approved |
| Fairness testing of credit decisions | The assistant makes no credit decisions. If that changes, this is reopened |
| Training or fine-tuning a model on Fernleaf data | Not needed; and it would make erasure of a person's data from the model impractical |
| Labelling under the IT Rules amendment on synthetically generated information (in force from 20 February 2026) | Applies to intermediaries and synthetic audio, video and images; a text chat inside Fernleaf's own app is not in scope. General Counsel to confirm |
| Conformity with the EU AI Act | Fernleaf serves borrowers in India only |
| Using AgentCore Evaluations on real conversations | From Mumbai it may route prompts to any AWS region. Fernleaf's own test harness is used instead, through the India profile |

---

Not legal advice. The decisions are a worked example for a fictional company.
