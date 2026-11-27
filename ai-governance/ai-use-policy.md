# Policy on the use of AI

Fernleaf Finance (fictional). Policy 19 in `operating-model/policy-index.md`. Owner: CTO. Approved by: the privacy committee, then the board of directors. Reviewed: every year, and when a new AI system or staff AI tool is proposed.

The Act does not mention AI. It applies to AI in the same way as to any other processing: the company answers for every use of personal data, by its own systems, by its people, and by its providers (Section 8(1)). This policy says how that is done for AI.

---

## 1. Scope

- **AI systems the company builds or runs**, such as the borrower assistant.
- **AI tools staff use at work**, including public chatbots, AI features inside the products the company already uses, and AI note-takers.
- **AI features switched on by a vendor** inside a service that processes Fernleaf's personal data.

## 2. Rules for everyone

1. **No personal data in an AI tool that is not approved for it.** Customer and employee data, including Aadhaar, PAN, account numbers, phone numbers and the contents of complaints, may be used only in an AI tool the AI register lists as approved for personal data. On publication, there is none (decision D-7).
2. **Public chatbots** may be used for work that contains no personal data. The browser masks personal data before a prompt is sent, and uploads of customer files are blocked. Masking is a safety net, not permission.
3. **No AI note-takers on customer calls.** A note-taker would make a new copy of what customers say, outside the personal data register and with a provider that has no contract with Fernleaf.
4. **Report a mistake at once.** If personal data was sent to an AI tool that is not approved for it, tell the CISO the same day. It is handled as a possible personal data breach under the breach procedure. The Rules set no threshold of seriousness below which a breach need not be intimated (Rule 7).

## 3. Rules for AI systems the company builds or runs

1. **In the AI register before any build starts**, with an accountable role, a purpose, a risk tier, and the personal data it uses. `tools/ai_register_check.py` must pass.
2. **Only data the personal data register knows about**, for a purpose recorded there, and never children's data.
3. **Rules that matter are enforced outside the model:** which customer's data a tool may read; which tools are allowed; which actions a person must approve.
4. **Personal data is masked** before it reaches the model and before anything is logged. Logs of processing are kept for a year (Rule 6(1)(e)).
5. **Customers are told** when they are talking to an AI, and can ask for a person at any time.
6. **A named role can suspend it** at once, in two steps: read-only, and halt.
7. **Independent validation before deployment**, by the Chief Risk Officer, and again after any change to the model, the tools or the prompts.
8. **An impact assessment** before build, reviewed before deployment.
9. **Models run in India.** Through an inference profile that keeps processing in India, under a contract with the provider. The provider's terms on training and retention are confirmed in writing.

## 4. Rules for vendors

A vendor may not switch on an AI feature that processes Fernleaf's personal data without notice and approval. That is a change to the processing under its contract (Section 8(2), Rule 6(1)(f)), decided as any new processing by a Data Processor (charter, section 5).

## 5. Exceptions

An exception to this policy follows the exceptions procedure: the system owner decides, the CISO must agree, and it expires within 90 days. No exception is possible for rules 2.1, 3.2 or 3.5.

---

Not legal advice. The policy is a worked example for a fictional company.
