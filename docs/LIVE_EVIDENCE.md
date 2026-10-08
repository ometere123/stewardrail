# Studionet live evidence index

The machine-readable records in `deploy/proofs/` distinguish fresh observations
from historical records at chain 61999.

Observed evidence:

- `deployment.json` records the five finalized deployment transactions and the
  exact source hashes used for the corrected deployment.
- `fresh-correction-live.json` records the fresh mandate readback and a finalized
  deterministic refusal against that deployment.
- `live-scenarios.json` and `live-final-hardening.json` are historical records
  for earlier source deployments and are explicitly not final-deployment proof.

The required appeal reversals and Vault payout are explicitly marked
`not_observed`. An appeal attempt finalized with execution `ERROR` and consensus
`MAJORITY_DISAGREE`; it is not presented as a successful reversal. No payout is
claimed without a finalized terminal allow and successful Vault execution.
