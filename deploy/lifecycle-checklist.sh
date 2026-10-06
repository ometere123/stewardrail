#!/usr/bin/env bash
set -euo pipefail
cat <<'EOF'
Run docs/LIVE_TEST_PLAN.md exactly. Minimum proof rows:
  01 threshold mandate activation
  02 issuer attestation
  03 deterministic refuse
  04 semantic primary allow/refuse
  05 allow -> appeal -> refuse
  06 refused payout attempt
  07 refuse -> appeal -> allow
  08 successful exact payout
  09 duplicate payout refusal
  10 threshold recovery
For every write: capture transaction hash, FINALIZED status, execution result,
state after finalization, and explorer URL in deploy/proofs/*.json.
EOF
