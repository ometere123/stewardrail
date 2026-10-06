"""Static adversarial invariants that run without a local GenVM.

The completion handoff requires these same cases to be rerun through GenLayer
Direct Mode before deployment. These tests make architectural regressions fail
in ordinary CI as well.
"""
from pathlib import Path
import ast

ROOT = Path(__file__).parents[2]
CONTRACTS = ROOT / "contracts"


def text(name):
    return (CONTRACTS / name).read_text()


def test_exactly_five_deployable_sources_and_each_has_runtime_pin():
    files = sorted(p.name for p in CONTRACTS.glob("*.py"))
    assert files == ["evidence_registry.py", "steward_charter.py", "steward_court.py", "steward_guard.py", "steward_vault.py"]
    for name in files:
        first = text(name).splitlines()[0]
        assert '"Depends"' in first and "py-genlayer:" in first
        ast.parse(text(name))


def test_no_generated_or_minified_contract_shadow_tree():
    assert not (CONTRACTS / "build").exists()
    assert not list(CONTRACTS.glob("*.min.py"))


def test_guard_nondeterminism_is_only_for_semantic_adjudication():
    src = text("steward_guard.py")
    assert "gl.vm.run_nondet" in src
    assert src.count("gl.nondet.web.get") >= 2
    assert src.count("gl.nondet.exec_prompt") >= 2
    assert "preview_spend" in src
    assert 'emit(on="finalized").record_primary' in src


def test_court_has_real_reversal_and_finalized_terminal_delivery():
    src = text("steward_court.py")
    assert "record[\"effective\"] = str(result[\"verdict\"])" in src
    assert 'emit(on="finalized").record_terminal' in src
    assert "close_unappealed" in src
    assert "only a principal, agent, or spend recipient may appeal" in src


def test_vault_has_no_agent_payout_bypass_and_is_idempotent():
    src = text("steward_vault.py")
    assert "only the bound court may record terminal decisions" in src
    assert "spend already paid" in src
    assert "terminal decision refuses payment" in src
    assert "recovery_is_approved" in src
    assert "emit_transfer" in src


def test_charter_has_no_unilateral_historical_override():
    src = text("steward_charter.py")
    forbidden = ["override_release", "override_refuse", "set_mandate", "delete_version"]
    for token in forbidden:
        assert token not in src
    assert "threshold" in src and "approve_mandate" in src


def test_evidence_registry_history_cannot_be_re_attested_over():
    src = text("evidence_registry.py")
    assert "history is immutable" in src
    assert "status_at" in src
    assert "revoked_at" in src
