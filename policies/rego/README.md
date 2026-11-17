# Plan-check rules (Release 3, Prevent)

Every infrastructure change is planned with Terraform, and the plan is checked against these rules before anything is applied. A plan that breaks a rule is stopped; nothing reaches AWS.

| File | What it is |
|---|---|
| `prevent.rego` | The rules. Each denial starts with the provision it serves |
| `prevent_test.rego` | Unit tests: a compliant plan passes, and each kind of non-compliant change is denied with the right provision |

## The rules

| Message starts with | Rule | Provision |
|---|---|---|
| `[s.8(1)]` | Every bucket and table carries `DataClass` (`personal` or `none`); a personal store carries `RegisterStore`, naming an entry in `register/personal-data-register.yaml` | Act, Section 8(1) |
| `[R.6(1)(b)]` | Every bucket has a fixed name and a public access block with all four settings on | Rules, Rule 6(1)(b) |
| `[R.6(1)(d)]` | Personal buckets are versioned; personal tables have point-in-time recovery | Rules, Rule 6(1)(d) |
| `[R.6(1)(e)]` | Log groups keep logs for at least 365 days, or never expire | Rules, Rule 6(1)(e) |
| `[Mumbai only]` | Every AWS provider sets `region = "ap-south-1"` as a fixed value | Design choice of this build |

Encryption at rest is not checked: S3 has encrypted every new object by default since January 2023, and DynamoDB always encrypts its tables, so such a rule would always pass.

## Running them

```bash
scripts/plan_check.sh terraform/live/workload/model-company            # plan and check
scripts/plan_check.sh terraform/live/workload/model-company --apply    # ... then apply
conftest verify --policy policies/rego                                  # the unit tests
```

The rules read the plan as JSON (`terraform show -json`) and the register as data (`data.stores`). They are written in Rego v1 syntax (`import rego.v1`) and run by conftest, whose version is pinned in `config/tool-versions.env`.

## Changing a rule

A rule changes through the same process as any other change: a pull request, with a unit test in `prevent_test.rego` that fails without the change and passes with it, reviewed and approved by someone other than the author, with the DPO consulted. The same rule must also be changed in AWS Config (`terraform/modules/detective-controls`), so that the check before a change and the check after it stay the same.
