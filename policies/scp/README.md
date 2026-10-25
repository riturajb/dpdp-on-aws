# Guardrail policies

Service control policies set limits that nobody in a member account can exceed, including its
administrators. They never give permission; they only take it away. They do not apply to the
management account, which is why a faulty guardrail can always be detached from there.

They are created by `terraform/live/management/organization` and attached in three stages
(setup guide, Part 9). JSON allows no comments, so each statement is explained here.

| Policy (short name) | Attached to | Statement | What it stops | Why |
|---|---|---|---|---|
| `deny-regions-outside-mumbai` (region) | Sandbox, Workloads, Security | DenyAllRegionsExceptMumbai | Any action in a region other than Mumbai, except global services such as IAM, Organizations, billing and sign-in, which AWS runs outside any one region | Keeps data in India, as RBI requires for payment system data (the wallet), and prevents costly mistakes in other regions. DPDP itself does not require data to stay in India (Section 16) |
| `baseline-protections` (baseline) | Sandbox, Workloads, Security | DenyLeavingTheOrganization | An account removing itself from the organisation | An account outside the organisation escapes every guardrail |
| | | ProtectTheAuditTrail | Stopping, deleting or changing CloudTrail trails | Rule 6(1)(c): access logs must keep being recorded |
| | | DenyTheRootUser | Any action by an account's root user, except root tasks run centrally from the management account | Root has unlimited power and no named owner; daily work uses Identity Center roles |
| `protect-log-and-evidence-buckets` (buckets) | Workloads, Security | NoDeletionOrWeakeningOfLogsAndEvidence | Deleting log or evidence files or buckets; bypassing or shortening their lock; switching off versioning; adding lifecycle rules; changing their policy, encryption, ownership, access lists, public access settings or replication | Rule 6(1)(e): logs kept for a year and evidence that cannot be altered, even by an administrator. Attach only after the buckets exist |
| `deny-costly-services` (cost) | Sandbox, Workloads | DenyNatGateways | Creating NAT gateways | About USD 32 a month each, even when idle |
| | | DenyLargeInstances | Starting servers larger than t3/t4g micro or small | Prevents an accidental large bill |
| | | DenyHighFixedCostServices | OpenSearch, MSK, Redshift, SageMaker endpoints, RDS, ElastiCache | Services with a fixed monthly cost that this project does not need |

**Changing a guardrail:** edit the JSON file, run `terraform plan` in the organisation stack, read
the plan, apply. To change a protected bucket: detach `buckets` from the Security unit, apply the
bucket change, attach it again. Every step is recorded by the organisation trail.
