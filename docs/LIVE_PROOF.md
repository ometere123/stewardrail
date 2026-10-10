# Live proof index

The current machine-readable packet is
[`deploy/proofs/final-source-stack-2026-10-10.json`](../deploy/proofs/final-source-stack-2026-10-10.json).

It records the source-matched six-contract Studionet stack, source hashes,
deployment and binding transactions, and the adversarial registration
reconciliation evidence. The direct-mode regressions cover registration retry,
registration expiry/refund, late acknowledgment rejection, late Guard/Vault
result rejection, replay and redelivery. A forced live child-delivery loss is
not claimed because the network does not provide a safe way to induce one.
Historical packets remain in `deploy/proofs/` with explicit superseded status.
