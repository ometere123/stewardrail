#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CLI=(npx --no-install genlayer)
"${CLI[@]}" --version | grep -q '0.39.1' || { echo 'Expected repository-local genlayer 0.39.1'; exit 1; }
"${CLI[@]}" network set studionet
"${CLI[@]}" network info
node deploy/network-check.mjs
python3 scripts/preflight.py

cat <<'EOF'
StewardRail deployment is intentionally interactive because four constructor
steps depend on addresses returned by previous deployments and the signer must
be the intended charter principal.

1) Charter
   npx --no-install genlayer deploy --contract contracts/steward_charter.py \
     --args '<principals-json>' <threshold> <agent-address> '<mandate-json>'

2) Registry
   npx --no-install genlayer deploy --contract contracts/evidence_registry.py

3) Court
   npx --no-install genlayer deploy --contract contracts/steward_court.py \
     --args <charter-address> <registry-address>

4) BondVault
   npx --no-install genlayer deploy --contract contracts/steward_bond_vault.py \
     --args <charter-address> <agent-address>

5) Guard
   npx --no-install genlayer deploy --contract contracts/steward_guard.py \
     --args <charter-address> <registry-address> <court-address>

6) Vault
   npx --no-install genlayer deploy --contract contracts/steward_vault.py \
     --args <charter-address> <guard-address> <court-address> <bond-vault-address>

7) Threshold binding
   Both principals approve `approve_bond_vault_binding(bond, guard, vault)`;
   then any caller may execute `BondVault.bind(guard, vault)` exactly once.

After every transaction, wait for FINALIZED and confirm successful execution.
Record addresses and tx hashes in deploy/deployments.json. Never continue from an
ACCEPTED-only receipt.
EOF
