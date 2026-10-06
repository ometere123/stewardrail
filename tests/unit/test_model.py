import json
from pathlib import Path
import pytest

from reference.model import (
    ALLOW, REFUSE, HELD, HistoricalSpend, appeal_effective, classify,
    evidence_active_at, issuer_authorized, origin, validate_mandate, vault_can_pay,
)

MANDATE = json.loads((Path(__file__).parents[1] / "fixtures" / "mandate.json").read_text())
RECIPIENT = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def test_fixture_is_valid():
    validate_mandate(MANDATE)


def test_max_per_spend_refuses_without_semantics():
    got = classify(MANDATE, 6 * 10**18, RECIPIENT, "creative", 1000, [])
    assert got == {"state": REFUSE, "rules": ["max_per_spend"]}


def test_rolling_exposure_refuses():
    history = [HistoricalSpend(4 * 10**18, 990, ALLOW), HistoricalSpend(4 * 10**18, 995, HELD)]
    got = classify(MANDATE, 5 * 10**18, RECIPIENT, "creative", 1000, history)
    assert got["state"] == REFUSE and got["rules"] == ["rolling_limit"]


def test_refused_history_does_not_consume_exposure():
    history = [HistoricalSpend(9 * 10**18, 990, REFUSE)]
    got = classify(MANDATE, 2 * 10**18, RECIPIENT, "creative", 1000, history)
    assert got["state"] == HELD


def test_small_spend_can_clear_without_jury():
    got = classify(MANDATE, 5 * 10**17, RECIPIENT, "creative", 1000, [])
    assert got == {"state": ALLOW, "rules": []}


def test_semantic_trigger_holds():
    got = classify(MANDATE, 2 * 10**18, RECIPIENT, "creative", 1000, [])
    assert got == {"state": HELD, "rules": ["brief-fit"]}


def test_multiple_semantic_rules_are_frozen_together():
    got = classify(MANDATE, 2 * 10**18, RECIPIENT, "research", 1000, [])
    assert got == {"state": HELD, "rules": ["brief-fit", "independent-proof"]}


def test_category_allowlist_refuses_first():
    got = classify(MANDATE, 1, RECIPIENT, "gambling", 1000, [])
    assert got == {"state": REFUSE, "rules": ["category_allowlist"]}


def test_denylisted_recipient_refuses():
    got = classify(MANDATE, 1, "0x9999999999999999999999999999999999999999", "creative", 1000, [])
    assert got == {"state": REFUSE, "rules": ["recipient_denylist"]}


def test_origin_exact_host_only():
    assert origin("https://vendor.example/invoice/1") == "https://vendor.example"
    assert origin("https://vendor.example.evil.test/x") == "https://vendor.example.evil.test"
    assert origin("http://vendor.example/x") == ""
    assert origin("https://user@vendor.example/x") == ""


def test_issuer_requires_wallet_role_and_exact_origin():
    assert issuer_authorized(MANDATE, "0x1111111111111111111111111111111111111111", "vendor", "https://vendor.example/a")
    assert not issuer_authorized(MANDATE, "0x1111111111111111111111111111111111111111", "auditor", "https://vendor.example/a")
    assert not issuer_authorized(MANDATE, "0x1111111111111111111111111111111111111111", "vendor", "https://vendor.example.evil.test/a")


def test_historical_attestation_survives_later_revocation():
    assert evidence_active_at(100, 200, 150)
    assert not evidence_active_at(100, 200, 250)
    assert evidence_active_at(100, 0, 250)
    assert not evidence_active_at(200, 0, 150)

@pytest.mark.parametrize("primary,appeal,expected", [
    (ALLOW, None, ALLOW),
    (REFUSE, None, REFUSE),
    (ALLOW, REFUSE, REFUSE),
    (REFUSE, ALLOW, ALLOW),
])
def test_appeal_can_affirm_or_reverse_both_directions(primary, appeal, expected):
    assert appeal_effective(primary, appeal) == expected


def test_vault_only_pays_terminal_allow_once():
    assert not vault_can_pay(None, False)
    assert not vault_can_pay({"decision": REFUSE, "amount": 10}, False)
    assert vault_can_pay({"decision": ALLOW, "amount": 10}, False)
    assert not vault_can_pay({"decision": ALLOW, "amount": 10}, True)


def test_missing_issuer_role_is_invalid():
    broken = json.loads(json.dumps(MANDATE))
    broken["issuers"] = broken["issuers"][:2]
    with pytest.raises(ValueError, match="uncovered role"):
        validate_mandate(broken)
