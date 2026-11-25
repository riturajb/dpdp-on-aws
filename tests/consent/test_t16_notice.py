"""T16: the notice matches the register and contains everything Rule 3 requires.

Control:          DPDP-Act-S5(1)
What is checked:  tools/notice.py puts the wording together with the register's lists, in
                  English and Hindi, and checks the result: every purpose that relies on consent is a separate choice,
                  with its itemised data, the purpose and what it enables (Rule 3(b)); the
                  links to withdraw consent, exercise rights and complain to the Board (Rule
                  3(c)); the contact who answers questions (Section 6(3)); both languages
                  complete (Section 5(3)); no reference to another document (Rule 3(a)).
                  Then two broken copies of the register must fail: one with a purpose that
                  has no Hindi text, one with no link to withdraw consent.
Pass means:       The notice is complete in both languages, and the check catches an
                  incomplete one.
Fail means:       A person could be asked for consent without the information Rule 3 requires.
Evidence stored:  Locally (offline test, also run in GitHub Actions).
Who runs it:      Anyone, with no AWS access; also GitHub Actions on every pull request.
When:             Release 4, Steps 1 and 8; after every change to the register.
Changes AWS:      No.
"""
import copy

from tools import notice, register


def test_t16_notice_meets_rule_3(record):
    reg = register.load()
    built = notice.build(reg)
    problems = notice.check(reg, built)

    # The same notice always gets the same version name; a changed notice gets a new one.
    same = notice.version(notice.build(reg)) == notice.version(built)

    # Broken copy 1: a purpose without its Hindi text.
    no_hindi = copy.deepcopy(reg)
    del no_hindi["data_categories"][0]["purposes"][0]["purpose_hi"]
    caught_hindi = [p for p in notice.check(no_hindi, notice.build(no_hindi))
                    if p.startswith("[Rule 3(b)(ii)]")]
    changed = notice.version(notice.build(no_hindi)) != notice.version(built)

    # Broken copy 2: no link to withdraw consent.
    no_link = copy.deepcopy(reg)
    no_link["notice"]["links"]["withdraw"] = ""
    caught_link = [p for p in notice.check(no_link, notice.build(no_link))
                   if p.startswith("[Rule 3(c)(i)]")]

    ok = not problems and same and changed and bool(caught_hindi) and bool(caught_link)
    response = (f"notice {notice.version(built)}: {len(built['choices'])} choices, languages "
                f"{', '.join(built['languages'])}; problems: {'; '.join(problems) or 'none'}; "
                f"same version on rebuild: {same}; new version when changed: {changed}; "
                f"missing Hindi caught: {bool(caught_hindi)}; missing withdraw link caught: "
                f"{bool(caught_link)}")
    record("DPDP-Act-S5(1)", "t16-notice-meets-rule-3",
           "Check the notice against Rule 3 and the register, then check two "
           "broken copies", response, "PASS" if ok else "FAIL", account="offline")
    assert ok, response
