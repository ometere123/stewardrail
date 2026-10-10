# Studionet live evidence

The canonical current record is
[`deploy/proofs/final-release-2026-10-10.json`](../deploy/proofs/final-release-2026-10-10.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment and threshold-binding receipts, the
active two-principal mandate, exact source hashes, and a funded current-source
lifecycle. Spend `1` reached semantic `ALLOW`, finalized through Court → Guard
→ BondVault lock/confirmation → Vault, and paid 1 GEN from a 20 GEN treasury
fund. The payout finalized with `value_credited: true`. Spend `0` produced a
finalized semantic `REFUSE`. Spend `3` completed a bonded challenge through
Court, Guard, Vault and BondVault; the 0.05 GEN bond was refunded once. Two
later finalized reconciliation calls emitted no payable child and left the
BondVault and Vault balances unchanged.

The validator network does not expose a safe control for deliberately dropping
one internal child, so the lost-acknowledgment branch is not represented as a
forced live observation. Earlier packets are retained for audit history and
are explicitly marked `historical-superseded`.
