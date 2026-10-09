# Studionet live evidence index

The machine-readable records in `deploy/proofs/` distinguish fresh observations
from historical records at chain 61999.

Observed evidence:

- `canonical-deployment-2026-10-09.json` records the six fresh finalized deployment
  transactions, exact source hashes, principal actors, mandate activation and
  threshold-approved BondVault binding for the current source commit.
- `deployments.json` is the canonical address and transaction index consumed by
  release tooling.
- `deployment.json`, `fresh-correction-live.json`, `live-scenarios.json` and
  `live-final-hardening.json` are historical records for earlier source
  deployments and are explicitly not current-deployment proof.

No fresh spend, evidence, challenge, appeal reversal, payout, recovery, or
recipient balance delta is claimed for the current stack until its own finalized
transactions are recorded. An earlier appeal attempt finalized with execution
`ERROR` and is not presented as a successful reversal.
