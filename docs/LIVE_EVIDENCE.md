# Studionet live evidence index

The machine-readable records in `deploy/proofs/` distinguish fresh observations
from historical records at chain 61999.

Current evidence:

- `final-fresh-studionet-2026-10-10.json` is the current packet for the six exact
  sources and addresses in `deploy/deployments.json`.
- It records finalized deployment/binding receipts, threshold activation,
  authenticated issuer attestations, nested terminal delivery and duplicate
  payout rejection.
- The payout and recovery EOA children are recorded as value credited with
  `NO_MAJORITY`; this is an explicit network limitation, not a success claim.

Historical evidence:

- `canonical-deployment-2026-10-09.json` records a historical six-contract stack
  from an earlier source generation. It is superseded and is not the current
  deployment for this checkout.
- `deployments.json` is the current canonical deployment index.
- `deployment.json`, `fresh-correction-live.json`, `live-scenarios.json` and
  `live-final-hardening.json` are historical records for earlier source
  deployments and are explicitly not current-deployment proof.

An earlier appeal attempt finalized with execution `ERROR` and is not presented as
a successful reversal. The current packet explicitly lists unobserved semantic
ALLOW consensus, reversals, single-use replay, rolling reversal, challenge
settlement, threshold recovery and post-payment clawback rather than inferring them.
