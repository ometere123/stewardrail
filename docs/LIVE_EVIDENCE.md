# Studionet live evidence index

The machine-readable records in `deploy/proofs/` distinguish fresh observations
from historical records at chain 61999.

Observed evidence:

- `canonical-deployment-2026-10-09.json` records a historical six-contract stack
  from an earlier source generation. It is superseded and is not the current
  deployment for this checkout.
- `deployments.json` retains that historical transaction index for auditability;
  it must not be used as the current frontend or release address source.
- `deployment.json`, `fresh-correction-live.json`, `live-scenarios.json` and
  `live-final-hardening.json` are historical records for earlier source
  deployments and are explicitly not current-deployment proof.

No current deployment is declared until the exact six current sources have been
deployed and each deployment has a FINALIZED, successful execution readback. No
fresh spend, evidence, challenge, appeal reversal, payout, recovery, or recipient
balance delta is claimed before that deployment. An earlier appeal attempt
finalized with execution `ERROR` and is not presented as a successful reversal.
