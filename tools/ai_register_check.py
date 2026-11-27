"""Check the AI register against the personal data register.

  python tools/ai_register_check.py                      # the AI register in this repository
  python tools/ai_register_check.py --ai-register FILE   # another AI register file

Exit code 0 = no FAIL. Exit code 1 = at least one FAIL. WARN lines are open items.

What:        Prints every finding of tools/ai_register.py (FAIL first, then WARN) and a result
             line. The rules are listed in the header of tools/ai_register.py.
Why:         DPDP Act s.4, s.8(1), s.8(5), s.9 and Rule 6(1): an AI system may only use personal
             data the company has recorded, for a recorded purpose, with safeguards. RBI draft
             guidance on model risk management (June 2026): a model inventory with owners,
             validators and tiers; human oversight; the ability to suspend.
Who runs it: Anyone, offline. GitHub Actions runs it on every pull request, and the pre-commit
             hook runs it whenever a file under register/ changes.
When:        AI governance companion release (v0.5.1), Step 2; after every change to either
             register.
Reads:       register/ai-register.yaml and register/personal-data-register.yaml.
Writes:      Nothing.
Changes AWS: No.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import ai_register, register  # noqa: E402


def main(argv=None) -> int:
    """Run the checks, print each finding, and return 1 if any FAIL was found (used by CI)."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ai-register", default=str(ai_register.DEFAULT_AI_REGISTER))
    ap.add_argument("--register", default=str(register.DEFAULT_REGISTER))
    args = ap.parse_args(argv)

    ai = ai_register.load(args.ai_register)
    findings = ai_register.check(ai, register.load(args.register))
    fails = [f for f in findings if f.level == "FAIL"]
    warns = [f for f in findings if f.level == "WARN"]
    print(f"AI register: {args.ai_register}")
    print(f"AI systems: {len(ai.get('systems') or [])}, models: {len(ai.get('models') or [])}, "
          f"staff AI tools: {len(ai.get('staff_tools') or [])}")
    for f in fails + warns:
        print(f"  {f}")
    print(f"Result: {'FAIL' if fails else 'PASS'} ({len(fails)} failures, {len(warns)} open items)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
