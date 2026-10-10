# Studionet live evidence

The canonical current record is
[`deploy/proofs/final-source-stack-2026-10-10.json`](../deploy/proofs/final-source-stack-2026-10-10.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment and threshold-binding receipts, the
active two-principal mandate, exact source hashes, corrected
registration-reconciliation evidence, and a funded current-source lifecycle.
Spend `0` reached semantic `ALLOW`, finalized through Court → Guard → BondVault
lock/confirmation → Vault, and paid exactly 1 GEN from a 2 GEN treasury fund.
The payout child finalized with `value_credited: true`; a second payment
finalized with the expected duplicate-payment error. The focused adversarial
suite proves that Court registration retries the BondVault acknowledgment before
its deadline and that a refunded registration cannot later produce Guard or
Vault consequences.

The validator network does not expose a safe control for deliberately dropping
one internal child, so the lost-acknowledgment branch is not represented as a
forced live observation. Earlier packets are retained for audit history and
are explicitly marked `historical-superseded`.
