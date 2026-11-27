# Impact assessment: the borrower assistant

Fernleaf Finance (fictional). Status: **draft, before build** (Release 12). Follows the template in `operating-model/dpia-template.md`, with two sections added for an AI system: what the assistant may do (section 11), and how it fails and is stopped (section 12).

Fernleaf Finance is not a Significant Data Fiduciary, so the Act does not require this assessment (Section 10(2)(c)(i) applies only to them). It is done because the processing uses new technology, faces customers, and can start a change to a borrower's loan. The RBI draft guidance on model risk management (24 June 2026, not final) also expects every model, including a third-party AI model, to be validated before it is used, and this assessment sets out what the validation must cover.

---

**1. The processing.** A chat assistant in the Fernleaf app for signed-in adult borrowers. It answers questions about the borrower's own loan, raises complaints in her name, and can ask for a change to her repayment date, which a collections officer approves. Business owner: Head of Customer Service. Privacy Lead: Head of Privacy. Systems: the loans and tickets tables (Release 1), the AI register entry `borrower-assistant` and the model entry `claude-in` (`register/ai-register.yaml`). Model: Claude through Amazon Bedrock's India inference profile, which processes requests only in Mumbai and Hyderabad.

**2. Purpose.**
- Answering a borrower's questions about her own loan: amounts due, dates, how to pay.
- Raising a complaint or a request in her name.
- Passing a request to change her repayment date to a person who decides.

**3. Legal basis.** Open: **decision D-3** (General Counsel decides, the Privacy Lead must agree). Two readings are possible, and the choice changes the notice:
- the assistant is another way of serving the loan she already has, under the existing purposes `loan-collections` (consent) and `complaint-handling` (Section 7(a)); or
- it is a new purpose, which needs its own entry in the personal data register, a new version of the notice (Release 4) and, if it rests on consent, her consent before first use.
Until D-3 is decided, the AI register carries the purpose `borrower-assistance` as an open item, and the build cannot start.

**4. Personal data.**

| Category | Used for | Source | Leaves India |
|---|---|---|---|
| Contact details | Addressing her; confirming her registered number | `customers-db` | No |
| Loan application and loan terms | Answering questions about her loan | `loans-db` | No |
| Repayments and collections | Amounts due, dates, the date-change request | `loans-db` | No |
| Support tickets | Raising and tracking complaints | `tickets-db` | No |
| Conversations with the assistant (new) | The record of what she asked and what was answered | New store, Release 12 (decision D-4) | No |

Not used: credit bureau reports, Aadhaar and PAN, app events, teen wallet accounts. Whose data: adult borrowers only. Model calls are processed in Mumbai and Hyderabad. The provider of the model service (AWS) becomes a Data Processor and is added to the vendor list, with its contract clause, before the build (decision D-5).

**5. Rights of Data Principals.**
- **Notice:** the assistant says it is an AI at the start of every conversation, and links to the notice. If D-3 makes it a new purpose, the notice gains a new choice.
- **Withdrawal:** if the assistant rests on consent, withdrawal switches it off for her, and her conversations are erased at the end of their retention period.
- **Access, correction, erasure:** her conversations are part of the summary under Section 11 (Release 10), and erased with her other data, at Fernleaf and at the provider.
- **Grievance:** she can ask for a person at any point, and the assistant can raise a complaint, but never closes one.

**6. Risks to the rights of Data Principals, and how each is managed.**

| Risk to the person | Likelihood | Severity | Measure | Remaining risk |
|---|---|---|---|---|
| The assistant shows one borrower another borrower's loan | Medium | High | The customer id comes from the signed-in session in the tool code, never from the conversation; every tool is limited to that customer; tested in Release 13 (cross-customer access) | Low |
| A message tricks the assistant into using a forbidden tool, such as the credit score | Medium | High | Tools allowed or forbidden in a policy engine outside the model; `get_credit_score` and `waive_charges` forbidden; tested in Release 13 (prompt injection, tool misuse) | Low |
| The assistant changes her repayment date wrongly | Low | High | It can only ask; a collections officer approves every change; every request, decision and approval is a locked record | Low |
| The assistant gives a wrong amount or date, and she relies on it | Medium | Medium | Amounts and dates come from the tools, not from the model's memory; the reply shows the source; a person is offered on request; replies are sampled weekly | Medium; accepted by the business owner |
| Her Aadhaar, PAN or account number end up in logs or at the provider | Medium | High | Masked in the tool code before the model and before logging; model invocation logging off; Guardrails patterns as a second line | Low |
| Her conversations are kept or used by the provider beyond Fernleaf's purpose | Low | High | Provider terms confirmed in writing before build: no training on prompts, and what is stored for abuse detection, where and for how long (model entry `provider_data_terms`) | Medium until confirmed |
| She does not know she is talking to an AI, or cannot reach a person | Low | Medium | Disclosure at the start; a person on request; both checked by `tools/ai_register_check.py` | Low |
| A teen uses the assistant | Low | High | Available only to signed-in adult borrowers; teen accounts cannot open it | Low |

**7. Necessity.** Credit bureau data, KYC documents and app events were considered and left out: none is needed to answer a service question. Free-text search of all her tickets was considered and limited to her open tickets.

**8. Retention.** Conversations: a period to be set in decision D-4, with the legal reason, and not less than one year for the logs of processing (Rule 6(1)(e), Rule 8(3)). Traces: 365 days, masked. Locked action records: as the consent records, at least as long as the processing they prove.

**9. Security safeguards.** As for every personal data store (Releases 1 to 3), plus: masking before the model and before logging (Rule 6(1)(a)); a dedicated role for the assistant with access only to its tools (Rule 6(1)(b)); masked traces kept a year and a locked record of every action (Rule 6(1)(c), (e)); a read-only switch and a halt switch (Rule 6(1)(d)); the provider's contract clause (Rule 6(1)(f)); validation before deployment and the attack tests of Release 13 (Rule 6(1)(g)).

**10. Algorithmic software.** Fernleaf Finance is not a Significant Data Fiduciary, so Rule 13(3) does not apply. The assistant makes no decision about a person.

**11. What the assistant may do.** Read her loan, repayments, contact details and open tickets; raise a complaint; ask for a repayment date change, which a person approves. It may not read credit bureau data, waive charges, or decide anything about her credit. The full list is in the AI register, and the check fails if a tool that changes something has no approval rule.

**12. How it fails, and how it is stopped.** Wrong answers, prompt injection, tool misuse, a provider outage, or a change in the provider's terms. The CISO can switch it to read-only (no change tools) or halt it (no tools); the business owner can trigger either; restarting needs the Chief Risk Officer. Both switches are drilled in Release 13.

**13. Decision.** Not yet: **proceed to build only when** decisions D-3, D-4 and D-5 are closed, the provider's data terms are confirmed in writing, and the Chief Risk Officer has agreed the validation plan. Signed (when complete): Head of Customer Service, Head of Privacy; section 9: CISO; validation plan: Chief Risk Officer.

**14. Review.** Before deployment, after the Release 13 tests, and whenever a tool, the model, the provider, or the people who can use it change.

---

Not legal advice. The worked example is for a fictional company; the legal bases and decisions shown are its own.
