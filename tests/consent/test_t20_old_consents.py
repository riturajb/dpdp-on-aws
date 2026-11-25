"""T20: every customer who consented before the notice existed is given the notice.

Control:          DPDP-Act-S5(2)
What is checked:  tools/old_consents.py lists the open adult accounts, whose consent was given
                  before the notice existed, and records the delivery of the current notice to
                  each one not yet covered. A second report must then show nobody waiting, with
                  closed and teen accounts left out and counted.
Pass means:       The company can show that each earlier customer has been given the notice.
Fail means:       Earlier customers could go on being processed without ever receiving the
                  notice Section 5(2) requires.
Evidence stored:  The evidence bucket for the target account.
Who runs it:      The author or reader: pytest --live (engineer profile).
When:             Release 4, Step 8; the clean-room run. In the workload account the deliveries
                  are recorded in Step 7, so the test finds nobody waiting and sends nothing.
Changes AWS:      Only for customers not yet covered: one locked delivery record each, for 365
                  days in the workload account. No message is sent to anyone. One evidence
                  record.
"""
import pytest

from tools import old_consents

pytestmark = pytest.mark.live


def test_t20_earlier_customers_given_the_notice(record, target_session, published):
    first = old_consents.campaign(target_session, send=True)
    second = old_consents.campaign(target_session, send=False)
    ok = (first["eligible"] > 0 and not first["failed"] and not second["waiting"]
          and second["covered"] == second["eligible"] and second["notice_version"] == published)
    response = (f"notice {second['notice_version']}: {second['eligible']} earlier customers; "
                f"recorded in this run {first['sent_now']}; failed {len(first['failed'])}; "
                f"covered {second['covered']}; still waiting {len(second['waiting'])}; left out "
                f"{second['left_out']}")
    record("DPDP-Act-S5(2)", "t20-earlier-customers-given-the-notice",
           "Record the notice for every customer who consented before it existed, then report",
           response, "PASS" if ok else "FAIL", session=target_session)
    assert ok, response
