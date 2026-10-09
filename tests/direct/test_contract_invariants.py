"""Static adversarial invariants that run without a local GenVM.

The completion handoff requires these same cases to be rerun through GenLayer
Direct Mode before deployment. These tests make architectural regressions fail
in ordinary CI as well.
"""
from pathlib import Path
import ast
import os

ROOT = Path(__file__).parents[2]
CONTRACTS = Path(os.environ.get("STEWARD_MUTANT_CONTRACTS", ROOT / "contracts"))


def text(name):
    return (CONTRACTS / name).read_text()


def test_exactly_five_deployable_sources_and_each_has_runtime_pin():
    files = sorted(p.name for p in CONTRACTS.glob("*.py"))
    assert files == ["evidence_registry.py", "steward_bond_vault.py", "steward_charter.py", "steward_court.py", "steward_guard.py", "steward_vault.py"]
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
    assert 'emit(on="finalized").apply_terminal_decision' in src
    assert "close_unappealed" in src
    assert "only a principal, agent, or spend recipient may appeal" in src


def test_vault_has_no_agent_payout_bypass_and_is_idempotent():
    src = text("steward_vault.py")
    assert "only the bound guard may record terminal economic decisions" in src
    assert "spend already paid" in src
    assert "terminal decision refuses payment" in src
    assert "recovery_is_approved" in src
    assert "emit_transfer" in src
    assert 'raise gl.vm.UserError("[EXPECTED] only the bound guard may apply challenge outcomes")' in src
    assert 'key = u256(int(challenge_id))\n        incoming = json.dumps({"challenge_id": int(challenge_id)' in src


def test_bond_vault_is_narrow_and_guard_bound():
    src = text("steward_bond_vault.py")
    assert "only the bound vault may settle challenges" in src
    assert "if attempts >= max_attempts:" in src
    assert "only the configured agent may withdraw standing collateral" in src
    assert "quote_bond" in src and "open_challenge" in src and "settle" in src
    assert "gl.nondet" not in src
    assert 'raise gl.vm.UserError("[EXPECTED] collateral binding lacks threshold approval")' in src
    assert 'raise gl.vm.UserError("[EXPECTED] only the configured agent may withdraw standing collateral")' in src
    assert 'raise gl.vm.UserError("[EXPECTED] only the bound vault may settle challenges")' in src
    assert 'emit(on="finalized").open_challenge' in src
    assert 'emit(on="finalized").open_challenge(\n            _addr(self.guard), int(spend_id)' in src
    assert 'open_by_spend' in src
    assert 'return int(self.open_by_spend.get(u256(int(spend_id)), u256(0))) == 1' in src
    assert 'int(self.challenge_deadline[u256(challenge_id)])' in src
    assert 'raise gl.vm.UserError("[EXPECTED] an open challenge blocks payment")' in text("steward_vault.py")
    assert 'raise gl.vm.UserError("[EXPECTED] upheld challenge blocks payment")' in text("steward_vault.py")
    assert 'raise gl.vm.UserError("[EXPECTED] challenge policy bounds are invalid")' in text("steward_charter.py")
    assert 'floor = int(policy["bond_floor"])' in src
    assert 'raise gl.vm.UserError("[EXPECTED] only the bound court may apply challenge results")' in text("steward_guard.py")


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


def test_consequential_guards_remain_present():
    charter = text("steward_charter.py")
    registry = text("evidence_registry.py")
    court = text("steward_court.py")
    vault = text("steward_vault.py")
    assert "if int(self.principal_flag.get(caller, u256(0))) != 1:" in charter
    assert "if int(self.approved_proposal.get(key, u256(0))) == 1:" in charter
    assert "if int(self.recovery_approved_by.get(key, u256(0))) == 1:" in charter
    assert "attested <= stamp" in registry
    assert "revoked == 0 or revoked > stamp" in registry
    assert "if policy is None:" in court
    assert "if _origin(uri) not in allowed:" in court
    assert "if not bool(registry.status_at" in court
    assert 'emit(on="finalized").apply_terminal_decision' in court
    assert 'guard_target.emit(on="finalized").apply_challenge_result' in court
    assert "appeal cannot produce ALLOW without authenticated roles" in court
    assert "raise gl.vm.UserError(\"[EXPECTED] conflicting primary decision\")" in court
    assert "if gl.message.sender_address != self.guard:" in vault
    assert "raise gl.vm.UserError(\"[EXPECTED] conflicting terminal decision\")" in vault
    assert 'if str(record["decision"]) != ALLOW:' in vault
    assert "if int(self.paid.get(key, u256(0))) == 1:" in vault
    assert "if not approved:" in vault
    guard = text("steward_guard.py")
    assert "apply_terminal_decision" in guard
    assert "if gl.message.sender_address != self.court:" in guard
    assert 'raise gl.vm.UserError("[EXPECTED] only the bound court may apply terminal decisions")' in guard
    assert 'raise gl.vm.UserError("[EXPECTED] conflicting terminal authorization payload")' in guard
    assert "single-use evidence already consumed" in guard
    assert "if previous != \"\" and previous != str(int(spend_id)):" in guard
    assert "terminal authorization exposure exceeds mandate" in guard
    assert guard.count('vault_target.emit(on="finalized").record_terminal') == 2
    assert 'info.get("guard", "")) != _addr(gl.message.contract_address)' in guard
    assert 'raise gl.vm.UserError("[EXPECTED] vault binding mismatch")' in guard
    assert 'str(item.get("usage", "single_use")) != expected_usage' in guard
    assert 'semantic or self.state[key] != REFUSE' in guard
    assert "category must be 1..64 characters" in guard
    assert "terminal == ALLOW" in guard
    assert "amount_gte value must be a non-negative integer" in charter
    assert "unsupported semantic consequence" in charter
    assert "evidence_window_seconds must be 1..604800" in charter
    assert "approve_unfreeze" in charter and "unfreeze_is_approved" in charter
    assert "threshold approval has not authorized this unfreeze" in guard
    assert "self.revoked[prior_key] = u256(1)" in guard
    assert "revoked" in guard and "is_revoked" in guard
    assert 'if bool(gl.get_contract_at(self.guard).view().is_revoked(int(spend_id))):' in vault
    assert "terminal authorization has been revoked" in vault
    assert "evidence submission window is still open" in guard
    assert "only the charter agent may attach initial evidence" in guard
    assert "duplicate evidence identity" in guard
    assert "seal_evidence" in guard
    assert "raise gl.vm.UserError(\"[EXPECTED] evidence is sealed\")" in guard
