# Studionet live evidence

The canonical current record is
[`deploy/proofs/registration-reconciliation-stack-2026-10-10.json`](../deploy/proofs/registration-reconciliation-stack-2026-10-10.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment and threshold-binding receipts, the
active two-principal mandate, separate issuer attestations, a semantic
`ALLOW`, and the corrected source hashes. The focused adversarial suite proves
that Court registration retries the BondVault acknowledgment before its
deadline and that a refunded registration cannot later produce Guard or Vault
consequences.

The validator network does not expose a safe control for deliberately dropping
one internal child, so the lost-acknowledgment branch is not represented as a
forced live observation. Earlier packets are retained for audit history and
are explicitly marked `historical-superseded`.
