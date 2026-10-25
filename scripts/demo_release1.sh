#!/usr/bin/env bash
# Release 1 demonstration (Release 1 guide, Step 7).
#
# Runs the five checks live against AWS, prints a short version of each result, saves every result
# in notes/demo/<date>-<time>/, and makes a phone-sized video from the saved results:
# notes/demo/<date>-<time>/release1_demo.mp4. No screen recorder is needed.
#
# Before running: sign in (aws sso login --sso-session dpdp) and fill in config/local.env.
#   scripts/demo_release1.sh                       live run, then the video
#   scripts/demo_release1.sh --offline data/       steps 1 and 2 only, to try it without AWS
# The work is done by tools/demo_release1.py, which explains each step.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 tools/demo_release1.py run "$@"
