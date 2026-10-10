#!/usr/bin/env python3
"""Mutate exact deployable sources and require repository tests to kill each mutant."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"

MUTANTS = [
    ("charter-principal-gate", "steward_charter.py", "if int(self.principal_flag.get(caller, u256(0))) != 1:", "if False:"),
    ("charter-mandate-duplicate", "steward_charter.py", "if int(self.approved_proposal.get(key, u256(0))) == 1:", "if False:"),
    ("charter-recovery-duplicate", "steward_charter.py", "if int(self.recovery_approved_by.get(key, u256(0))) == 1:", "if False:"),
    ("registry-attested-before-request", "evidence_registry.py", "attested <= stamp", "attested >= stamp"),
    ("registry-revocation-history", "evidence_registry.py", "revoked == 0 or revoked > stamp", "revoked == 0 or revoked <= stamp"),
    ("court-issuer-role", "steward_court.py", "if policy is None:", "if False:"),
    ("court-exact-origin", "steward_court.py", "if _origin(uri) not in allowed:", "if False:"),
    ("court-attestation-provenance", "steward_court.py", "if not bool(registry.status_at", "if False and not bool(registry.status_at"),
    ("court-finalized-guard", "steward_court.py", 'emit(on="finalized").apply_terminal_decision', 'emit(on="accepted").apply_terminal_decision'),
    ("court-primary-conflict", "steward_court.py", 'raise gl.vm.UserError("[EXPECTED] conflicting primary decision")', "return"),
    ("vault-bound-guard", "steward_vault.py", 'raise gl.vm.UserError("[EXPECTED] only the bound guard may record terminal economic decisions")', "return"),
    ("vault-terminal-conflict", "steward_vault.py", 'raise gl.vm.UserError("[EXPECTED] conflicting terminal decision")', "return"),
    ("vault-terminal-allow", "steward_vault.py", 'if str(record["decision"]) != ALLOW:', "if False:"),
    ("vault-duplicate-payout", "steward_vault.py", "if int(self.paid.get(key, u256(0))) == 1:", "if False:"),
    ("vault-threshold-recovery", "steward_vault.py", "if not approved:", "if False:"),
    ("guard-terminal-court-binding", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] only the bound court may apply terminal decisions")', "return"),
    ("guard-terminal-conflict", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] conflicting terminal authorization payload")', "return"),
    ("guard-single-use-evidence", "steward_guard.py", 'if ((previous != "" and previous != str(int(spend_id)))', "if False:"),
    ("guard-terminal-vault-binding", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] vault binding mismatch")', "return"),
    ("guard-terminal-reservation", "steward_guard.py", 'terminal == ALLOW or (terminal == "" and (semantic or self.state[key] != REFUSE))', 'terminal == ALLOW'),
    ("guard-terminal-emission", "steward_guard.py", 'emit(on="finalized").record_terminal(', 'emit(on="accepted").record_terminal('),
    ("guard-category-bound", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] category must be 1..64 characters")', "return"),
    ("court-appeal-role-gate", "steward_court.py", 'raise gl.vm.UserError("[EXPECTED] appeal cannot produce ALLOW without authenticated roles: " + ",".join(missing))', "return"),
    ("charter-trigger-type", "steward_charter.py", 'raise gl.vm.UserError("[EXPECTED] amount_gte value must be a non-negative integer")', "return"),
    ("guard-usage-policy", "steward_guard.py", 'if str(item.get("usage", "single_use")) != expected_usage:', 'if False:'),
    ("charter-consequence-validation", "steward_charter.py", 'raise gl.vm.UserError("[EXPECTED] unsupported semantic consequence")', "return"),
    ("guard-unfreeze-threshold", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] threshold approval has not authorized this unfreeze")', "return"),
    ("guard-revocation-mark", "steward_guard.py", 'self.revoked[prior_key] = u256(1)', "self.revoked[prior_key] = u256(0)"),
    ("vault-revocation-check", "steward_vault.py", 'if bool(gl.get_contract_at(self.guard).view().is_revoked(int(spend_id))):', "if False:"),
    ("guard-evidence-deadline", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] evidence submission window is still open")', "return"),
    ("guard-evidence-agent-binding", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] only the charter agent may attach initial evidence")', "return"),
    ("guard-evidence-duplicate", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] duplicate evidence identity")', "return"),
    ("guard-evidence-seal", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] evidence is sealed")', "return"),
    ("charter-evidence-window-validation", "steward_charter.py", 'raise gl.vm.UserError("[EXPECTED] evidence_window_seconds must be 1..604800")', "return"),
    ("bond-binding-approval", "steward_bond_vault.py", 'raise gl.vm.UserError("[EXPECTED] collateral binding lacks threshold approval")', "return"),
    ("bond-agent-withdrawal", "steward_bond_vault.py", 'raise gl.vm.UserError("[EXPECTED] only the configured agent may withdraw standing collateral")', "return"),
    ("bond-vault-settlement", "steward_bond_vault.py", 'raise gl.vm.UserError("[EXPECTED] only the bound vault may settle challenges")', "return"),
    ("bond-court-finalized-open", "steward_bond_vault.py", 'emit(on="finalized").open_challenge(\n            _addr(self.guard), int(spend_id), challenge_id, _addr(self.vault), str(cause), int(self.challenge_deadline[u256(challenge_id)])', 'emit(on="accepted").open_challenge(\n            _addr(self.guard), int(spend_id), challenge_id, _addr(self.vault), str(cause), int(self.challenge_deadline[u256(challenge_id)])'),
    ("bond-indexed-open", "steward_bond_vault.py", 'return int(self.open_by_spend.get(u256(int(spend_id)), u256(0))) == 1', 'return False'),
    ("court-challenge-finalized-guard", "steward_court.py", 'guard_target.emit(on="finalized").apply_challenge_result', 'guard_target.emit(on="accepted").apply_challenge_result'),
    ("guard-challenge-court-binding", "steward_guard.py", 'raise gl.vm.UserError("[EXPECTED] only the bound court may apply challenge results")', 'return'),
    ("vault-challenge-guard-binding", "steward_vault.py", 'raise gl.vm.UserError("[EXPECTED] only the bound guard may apply challenge outcomes")', 'return'),
    ("vault-challenge-indexed", "steward_vault.py", 'key = u256(int(challenge_id))\n        incoming = json.dumps({"challenge_id": int(challenge_id), "upheld": bool(upheld)}, sort_keys=True)', 'key = u256(int(spend_id))\n        incoming = json.dumps({"challenge_id": int(challenge_id), "upheld": bool(upheld)}, sort_keys=True)'),
    ("vault-open-challenge-block", "steward_vault.py", 'raise gl.vm.UserError("[EXPECTED] an open challenge blocks payment")', "return"),
    ("vault-upheld-challenge-block", "steward_vault.py", 'raise gl.vm.UserError("[EXPECTED] upheld challenge blocks payment")', "return"),
    ("charter-challenge-schema", "steward_charter.py", 'raise gl.vm.UserError("[EXPECTED] challenge policy bounds are invalid")', "return"),
    ("bond-quote-floor", "steward_bond_vault.py", 'floor = int(policy["bond_floor"])', 'floor = 0'),
    ("bond-challenge-limit", "steward_bond_vault.py", 'if attempts >= max_attempts:', 'if False:'),
    ("bond-lock-full-coverage", "steward_bond_vault.py", 'secured = value if available >= value else 0', 'secured = min(value, available)'),
    ("bond-lock-expiry-gate", "steward_bond_vault.py", 'if deadline <= 0 or int(datetime.datetime.now().timestamp()) < deadline:\n            raise gl.vm.UserError("[EXPECTED] standing exposure challenge window is still open")', 'if False:'),
    ("bond-registration-ack-binding", "steward_bond_vault.py", 'if gl.message.sender_address != self.court:', 'if False:'),
    ("bond-registration-expiry-gate", "steward_bond_vault.py", 'if deadline <= 0 or int(datetime.datetime.now().timestamp()) < deadline:\n            raise gl.vm.UserError("[EXPECTED] challenge registration window is still open")', 'if False:'),
    ("guard-lock-ack-gate", "steward_guard.py", 'stored_economic == ALLOW and bond_vault != "" and lock_state != "confirmed"', 'False'),
    ("guard-confidence-floor", "steward_guard.py", 'raise gl.vm.UserError("[LLM_ERROR] semantic ALLOW confidence is below the mandate floor")', 'return result'),
    ("court-confidence-floor", "steward_court.py", 'raise gl.vm.UserError("[LLM_ERROR] semantic ALLOW confidence is below the mandate floor")', 'return result'),
    ("court-frozen-criteria-gate", "steward_court.py", 'if len(frozen_rules) == 0:', 'if False:'),
    ("court-challenge-digest-fail-closed", "steward_court.py", 'return json.dumps({"verdict": REFUSE, "confidence": 100, "reason": "challenge evidence digest mismatch"})', 'return json.dumps({"verdict": ALLOW, "confidence": 100, "reason": "challenge evidence digest mismatch"})'),
    ("court-challenge-unavailable-fail-closed", "steward_court.py", 'return json.dumps({"verdict": REFUSE, "confidence": 100, "reason": "challenge evidence unavailable"})', 'return json.dumps({"verdict": ALLOW, "confidence": 100, "reason": "challenge evidence unavailable"})'),
    ("bond-dismissal-keeps-lock", "steward_bond_vault.py", 'keep_lock_for_retry = (not bool(upheld)) and self._future_challenge_permitted(spend_id)', 'keep_lock_for_retry = False'),
    ("bond-dismissal-release-gate", "steward_bond_vault.py", 'if release_lock and locked_for_spend > 0:', 'if locked_for_spend > 0:'),
]


def main() -> None:
    killed = []
    with tempfile.TemporaryDirectory(prefix="stewardrail-mutants-") as tmp:
        mutant_dir = Path(tmp) / "contracts"
        for name, filename, needle, replacement in MUTANTS:
            if mutant_dir.exists():
                shutil.rmtree(mutant_dir)
            shutil.copytree(CONTRACTS, mutant_dir)
            path = mutant_dir / filename
            source = path.read_text(encoding="utf-8")
            count = source.count(needle)
            if count != 1:
                raise SystemExit(f"{name}: expected one mutation site, found {count}")
            path.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            env = os.environ.copy()
            env["STEWARD_MUTANT_CONTRACTS"] = str(mutant_dir)
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "tests/direct/test_contract_invariants.py"],
                cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
            )
            if result.returncode == 0:
                raise SystemExit(f"SURVIVED: {name}")
            killed.append(name)
            print(f"KILLED: {name}")
    print(f"mutation result: {len(killed)}/{len(MUTANTS)} killed (100%)")


if __name__ == "__main__":
    main()
