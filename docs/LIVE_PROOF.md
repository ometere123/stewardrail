# Live proof index

The current machine-readable packet is
[`deploy/proofs/final-source-stack-2026-10-10.json`](../deploy/proofs/final-source-stack-2026-10-10.json).

It records the source-matched six-contract Studionet stack, source hashes,
deployment and binding transactions, a funded semantic `ALLOW` lifecycle, and
the adversarial registration reconciliation evidence. Spend `0` finalized
through Court → Guard → BondVault lock/confirmation → Vault, was funded with 2
GEN, paid exactly 1 GEN, and produced a finalized `value_credited` transfer
child. A duplicate payment finalized with the expected error. The direct-mode
regressions cover registration retry, registration expiry/refund, late
acknowledgment rejection, late Guard/Vault result rejection, replay and
redelivery. A forced live child-delivery loss is not claimed because the
network does not provide a safe way to induce one.
Historical packets remain in `deploy/proofs/` with explicit superseded status.
