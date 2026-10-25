#!/usr/bin/env bash
# Adds a timestamped entry to the bootstrap log, and can save a command's output with it.
#
# Usage:
#   scripts/log_step.sh <part> "<what was done and why>"
#   scripts/log_step.sh <part> "<what was done and why>" -- <command and its arguments>
#
# Examples:
#   scripts/log_step.sh 5.3 "Root credentials of the four member accounts confirmed not present"
#   scripts/log_step.sh 3.5 "Trusted services before Part 4" -- aws organizations \
#     list-aws-service-access-for-organization --profile dpdp-mgmt-admin --output table
#
# The command runs in the current folder, so the script also works from inside a Terraform stack
# (call it there as ../../../../scripts/log_step.sh). Its output is shown on screen as usual.
# A copy is saved in notes/outputs/, and a line is added to the "Activity log" table in
# notes/bootstrap-log.md. A command that fails is still logged, with its exit code: for the
# guardrail tests, the refusal is the expected result.
# Git ignores notes/bootstrap-log.md, notes/outputs/ and notes/screenshots/, because they contain
# account ids (setup guide, Part 1.5).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"   # the repository folder

if [ $# -lt 2 ]; then
  sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
fi

PART="$1"
TEXT="${2//|//}"          # a | would break the Markdown table
shift 2

LOG="$ROOT/notes/bootstrap-log.md"
OUTDIR="$ROOT/notes/outputs"
mkdir -p "$OUTDIR" "$ROOT/notes/screenshots"

# First use: start the log from the template.
if [ ! -f "$LOG" ]; then
  cp "$ROOT/notes/bootstrap-log.template.md" "$LOG"
  echo "Started notes/bootstrap-log.md from the template."
fi

STAMP=$(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST')
SAVED="-"

# Optional command after --: run it, show its output, keep a copy.
if [ "${1:-}" = "--" ]; then
  shift
  if [ $# -eq 0 ]; then
    echo "Nothing to run after --." >&2
    exit 1
  fi
  NAME="$(TZ=Asia/Kolkata date '+%Y%m%d-%H%M%S')-part-${PART//\//-}.txt"
  [ -e "$OUTDIR/$NAME" ] && NAME="${NAME%.txt}-$$.txt"   # two entries in the same second
  FILE="$OUTDIR/$NAME"
  {
    echo "Part:    $PART"
    echo "Time:    $STAMP"
    echo "Note:    $TEXT"
    echo "Command: $*"
    echo
  } > "$FILE"
  "$@" 2>&1 | tee -a "$FILE"
  RC=${PIPESTATUS[0]}
  if [ "$RC" -ne 0 ]; then
    echo "(command ended with exit code $RC)" | tee -a "$FILE"
    TEXT="$TEXT (command ended with exit code $RC)"
  fi
  SAVED="\`notes/outputs/$NAME\`"
fi

printf '| %s | %s | %s | %s |\n' "$STAMP" "$PART" "$TEXT" "$SAVED" >> "$LOG"
echo
echo "Logged: $STAMP · Part $PART · $TEXT"
