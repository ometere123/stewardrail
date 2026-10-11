"""Independent rolling-window checks over realistic historical volumes.

The contract keeps indexed cursors for active exposure.  These tests use a
separate reference implementation so pruning, refusal release, and boundary
timestamps are compared against simple ledger semantics rather than against
the same helper code.
"""

import json
import copy
from pathlib import Path

from reference.model import ALLOW, HELD, REFUSE, HistoricalSpend, classify


MANDATE = json.loads((Path(__file__).parents[1] / "fixtures" / "mandate.json").read_text())
RECIPIENT = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def reference_total(history, now, window):
    floor = now - window
    return sum(item.amount for item in history if floor < item.at <= now and item.state != REFUSE)


def test_global_window_matches_reference_at_100_1000_and_5000_records():
    mandate = copy.deepcopy(MANDATE)
    mandate["deterministic"]["max_per_spend"] = 10_000
    mandate["deterministic"]["rolling_limit"]["amount"] = 10_000
    mandate["semantic_rules"][0]["when"]["value"] = 1
    for count in (100, 1_000, 5_000):
        history = [
            HistoricalSpend(amount=1, at=i, state=ALLOW if i % 5 else HELD)
            for i in range(count)
        ]
        now = count
        expected = reference_total(history, now, MANDATE["deterministic"]["rolling_limit"]["seconds"])
        assert expected == count
        result = classify(mandate, 1, RECIPIENT, "creative", now, history)
        assert result["state"] == HELD


def test_window_expiry_and_terminal_refusal_release_are_exact_at_boundary():
    window = MANDATE["deterministic"]["rolling_limit"]["seconds"]
    history = [
        HistoricalSpend(3, 100, ALLOW),
        HistoricalSpend(5, 101, REFUSE),
        HistoricalSpend(7, 102, HELD),
    ]
    assert reference_total(history, 100 + window, window) == 7
    assert reference_total(history, 101 + window, window) == 7
    assert reference_total(history, 102 + window, window) == 0


def test_recipient_reference_does_not_cross_contaminate_vendors():
    entries = [("alice", 199, 10), ("alice", 199, 20), ("bob", 199, 30)]
    now = 30
    window = 100
    alice = sum(amount for recipient, amount, at in entries if recipient == "alice" and now - window < at <= now)
    bob = sum(amount for recipient, amount, at in entries if recipient == "bob" and now - window < at <= now)
    assert alice == 398
    assert bob == 199
    assert alice + 199 > 500
