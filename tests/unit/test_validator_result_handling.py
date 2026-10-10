"""Focused checks for GenVM validator-result unwrapping and comparison."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.direct.genvm_stub import Runtime, load


ROOT = Path(__file__).resolve().parents[2]


class Return:
    def __init__(self, calldata):
        self.calldata = calldata


class UserError:
    pass


class VMError:
    pass


def _helpers(path: str):
    runtime = Runtime()
    namespace = load(ROOT / "contracts" / path, runtime)
    return namespace["_leader_payload"], namespace["_same_verdict"], namespace["_verdict"]


@pytest.mark.parametrize("path", ["steward_guard.py", "steward_court.py"])
def test_wrapped_return_with_same_verdict_agrees(path):
    _, same, _ = _helpers(path)
    assert same(Return({"verdict": "allow", "confidence": 95, "reason": "leader"}), {"verdict": "allow", "confidence": 88, "reason": "independent"})
    assert same(Return({"verdict": "refuse", "confidence": 95, "reason": "leader"}), {"verdict": "refuse", "confidence": 88, "reason": "independent"})


@pytest.mark.parametrize("path", ["steward_guard.py", "steward_court.py"])
def test_wrapped_return_with_different_verdict_disagrees(path):
    _, same, _ = _helpers(path)
    assert not same(Return({"verdict": "allow", "confidence": 95, "reason": "leader"}), {"verdict": "refuse", "confidence": 95, "reason": "independent"})
    assert not same(Return({"verdict": "refuse", "confidence": 95, "reason": "leader"}), {"verdict": "allow", "confidence": 95, "reason": "independent"})


@pytest.mark.parametrize("path", ["steward_guard.py", "steward_court.py"])
def test_reason_wording_does_not_change_decision(path):
    _, same, _ = _helpers(path)
    assert same(Return('{"verdict":"allow","confidence":95,"reason":"one"}'), '{"verdict":"allow","confidence":95,"reason":"different"}')


@pytest.mark.parametrize("path", ["steward_guard.py", "steward_court.py"])
def test_malformed_or_error_wrappers_fail_closed(path):
    payload, same, verdict = _helpers(path)
    assert payload(UserError()) is None
    assert payload(VMError()) is None
    assert not same(Return("not-json"), {"verdict": "allow", "confidence": 95})
    with pytest.raises(Exception, match="validator output"):
        verdict("not-json")


@pytest.mark.parametrize("path", ["steward_guard.py", "steward_court.py"])
def test_valid_allow_is_not_normalized_to_refuse(path):
    _, same, verdict = _helpers(path)
    parsed = verdict(Return({"verdict": "allow", "confidence": 95, "reason": "accepted"}).calldata)
    assert parsed["verdict"] == "allow"
    assert same(Return({"verdict": "allow", "confidence": 95}), {"verdict": "allow", "confidence": 95})


@pytest.mark.parametrize("path", ["steward_guard.py", "steward_court.py"])
def test_low_confidence_allow_keeps_its_semantic_verdict(path):
    """Confidence policy must reject unsafe ALLOW explicitly, never rewrite it to REFUSE."""
    _, _, verdict = _helpers(path)
    parsed = verdict({"verdict": "allow", "confidence": 40, "reason": "uncertain"})
    assert parsed["verdict"] == "allow"
    assert parsed["confidence"] == 40
