# Studionet live evidence

The canonical current record is
[`deploy/proofs/final-stack-2026-10-10.json`](../deploy/proofs/final-stack-2026-10-10.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment and binding receipts, two-principal
mandate activation, separate issuer attestations, a semantic `ALLOW`, the
finalized Court → Guard → Vault chain, a funded 0.1 GEN payment with a
finalized value-credit child, duplicate-payment rejection, and a post-payment
upheld challenge that reimbursed the Vault from standing collateral and
returned the challenger bond. A later reconciliation repeated the terminal
delivery idempotently.

A semantic `REFUSE` is not claimed in this packet. Older packets are retained
for audit history and are explicitly marked `historical-superseded`.
