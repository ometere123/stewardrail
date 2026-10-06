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
    ("court-finalized-terminal", "steward_court.py", 'target.emit(on="finalized").record_terminal', 'target.emit(on="accepted").record_terminal'),
    ("court-primary-conflict", "steward_court.py", 'raise gl.vm.UserError("[EXPECTED] conflicting primary decision")', "return"),
    ("vault-bound-court", "steward_vault.py", "if gl.message.sender_address != self.court:", "if False:"),
    ("vault-terminal-conflict", "steward_vault.py", 'raise gl.vm.UserError("[EXPECTED] conflicting terminal decision")', "return"),
    ("vault-terminal-allow", "steward_vault.py", 'if str(record["decision"]) != ALLOW:', "if False:"),
    ("vault-duplicate-payout", "steward_vault.py", "if int(self.paid.get(key, u256(0))) == 1:", "if False:"),
    ("vault-threshold-recovery", "steward_vault.py", "if not approved:", "if False:"),
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
