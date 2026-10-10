# Studionet live evidence

The canonical current record is
[`deploy/proofs/replay-safe-final-stack-2026-10-10.json`](../deploy/proofs/replay-safe-final-stack-2026-10-10.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment and threshold-binding receipts, the
active two-principal mandate, exact source hashes, and a funded current-source
lifecycle. Spend `1` reached semantic `ALLOW`, finalized through Court → Guard
→ BondVault lock/confirmation → Vault, and paid 0.1 GEN from a 2 GEN treasury
fund. The payout finalized with `value_credited: true`. The focused adversarial
suite proves that ordinary settlement reconciliation cannot emit another payable
child and that duplicate receiver credits reject without accepting value.

A fresh bonded settlement was not observed on this deployment because the
short challenge window elapsed after payout; older settlement packets remain
historical and are not relabeled as evidence for this source generation.

The validator network does not expose a safe control for deliberately dropping
one internal child, so the lost-acknowledgment branch is not represented as a
forced live observation. Earlier packets are retained for audit history and
are explicitly marked `historical-superseded`.
