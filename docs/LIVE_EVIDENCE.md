# Studionet live evidence index

The machine-readable records in `deploy/proofs/` contain only transactions and
readbacks observed on the fresh Studionet deployment at chain 61999.

Observed evidence:

- `deployment.json` records all five finalized deployment transactions and the
  exact source hashes used for the deployment.
- `live-scenarios.json` records threshold activation, issuer-attested evidence,
  deterministic refusal, and a finalized semantic refusal.

The required appeal reversals and Vault payout are explicitly marked
`not_observed`. An appeal attempt finalized with execution `ERROR` and consensus
`MAJORITY_DISAGREE`; it is not presented as a successful reversal. No payout is
claimed without a finalized terminal allow and successful Vault execution.
