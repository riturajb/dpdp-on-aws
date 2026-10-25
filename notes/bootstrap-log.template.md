# Bootstrap log

This is the record of every step that Terraform and the tests cannot record themselves: console steps, checks read on screen, values the guides ask you to keep, and decisions taken along the way. It is the evidence for the bootstrap of the platform.

**Private.** This file, `notes/outputs/` and `notes/screenshots/` contain account ids and email addresses. Git ignores them, so they are never committed. Keep a backup copy outside the laptop (setup guide, Part 1.5).

**How entries are made.** Never by typing in this file. Each entry is one command, shown at its step in the setup guide:

- `scripts/log_step.sh <part> "<what was done>"` adds a line.
- `scripts/log_step.sh <part> "<what this shows>" -- <command>` also runs the command and saves its output in `notes/outputs/`.
- A decision is a line that starts with `Decision:` and says what was decided and why.
- A screenshot is saved in `notes/screenshots/` under the name the guide gives, then logged with a line.

Decisions about the personal data register are logged here in the same way (Release 1 guide, Step 3).

---

## Activity log

Times are in IST.

| Date and time | Part | What was done, checked or decided | Saved output |
|---|---|---|---|
