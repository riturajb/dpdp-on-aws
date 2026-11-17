#!/usr/bin/env bash
# The gate every infrastructure change passes: plan, check the plan against the rules, and only
# then apply.
#
# What:        Runs "terraform plan" for one stack, converts the plan to JSON, and checks it with
#              conftest against policies/rego and the personal data register. If any rule is
#              broken, it stops: nothing is applied. With --apply, a plan that passes is applied
#              exactly as checked (the saved plan file, not a new plan).
# Why:         Rule 6 of the DPDP Rules requires the safeguards to be in place. Checking the plan
#              stops a non-compliant change before it reaches AWS (Release 3, Prevent).
# Who runs it: The engineer, for every change, instead of calling terraform apply directly.
#              Test T13 runs it against a deliberately non-compliant stack.
# When:        Release 3 onwards.
# Reads:       The stack's Terraform code and state; policies/rego; the register.
# Writes:      notes/plans/<stack>-<date>-<time>/ with tfplan, plan.json and check.txt
#              (ignored by Git: plans contain account ids).
# Changes AWS: Only with --apply, and only if the check passes.
#
#   scripts/plan_check.sh terraform/live/workload/model-company            # plan and check
#   scripts/plan_check.sh terraform/live/workload/model-company --apply    # ... then apply
#
# Exit codes: 0 passed (and applied, with --apply); 3 blocked by a rule; 1 any other error.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STACK="${1:?usage: scripts/plan_check.sh <stack folder> [--apply]}"
APPLY="${2:-}"
cd "$ROOT"
[ -d "$STACK" ] || { echo "STOP: no such folder: $STACK"; exit 1; }
command -v conftest >/dev/null || { echo "STOP: conftest is not installed. Run scripts/install_conftest.sh"; exit 1; }

NAME="$(echo "$STACK" | sed 's#^terraform/live/##; s#^tests/fixtures/##; s#/#-#g')"
OUT="$ROOT/notes/plans/${NAME}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"

# A stack is initialised once; its backend settings come from backend.hcl where there is one.
if [ ! -d "$STACK/.terraform" ]; then
  if [ -f "$STACK/backend.hcl" ]; then
    terraform -chdir="$STACK" init -input=false -backend-config=backend.hcl >/dev/null
  else
    terraform -chdir="$STACK" init -input=false >/dev/null
  fi
fi

echo "Plan: $STACK"
terraform -chdir="$STACK" plan -input=false -no-color -lock-timeout=60s -out="$OUT/tfplan" >"$OUT/plan.txt" \
  || { cat "$OUT/plan.txt"; echo "STOP: terraform plan failed."; exit 1; }
grep -E "^(Plan:|No changes)" "$OUT/plan.txt" || true
terraform -chdir="$STACK" show -json "$OUT/tfplan" >"$OUT/plan.json"

echo "Check: policies/rego against the plan"
set +e
conftest test "$OUT/plan.json" --policy policies/rego --data register/personal-data-register.yaml \
  --no-color | tee "$OUT/check.txt"
RC=${PIPESTATUS[0]}
set -e
if [ "$RC" -ne 0 ]; then
  echo "BLOCKED: the plan breaks the rules above. Nothing was applied."
  exit 3
fi
echo "PASS: the plan meets every rule."

if [ "$APPLY" = "--apply" ]; then
  terraform -chdir="$STACK" apply -input=false "$OUT/tfplan"
fi
