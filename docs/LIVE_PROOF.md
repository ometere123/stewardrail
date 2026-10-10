# Live proof index

The current machine-readable packet is
[`deploy/proofs/final-economic-lifecycle-2026-10-10.json`](../deploy/proofs/final-economic-lifecycle-2026-10-10.json).

It records the source-matched six-contract Studionet stack, source hashes,
deployment and binding transactions, threshold mandate activation, authenticated
issuer attestations, a semantic `ALLOW`, deterministic economic downgrade when
standing was unavailable, standing collateral funding, the nested finalized
authority chain, and a funded 1 GEN payment with a value-credited transfer
child. The adversarial direct-mode regressions cover registration retry,
registration expiry/refund, late acknowledgment rejection, late Guard/Vault
result rejection, replay and redelivery. A forced live child-delivery loss is
not claimed because the network does not provide a safe way to induce one.
Historical packets remain in `deploy/proofs/` with explicit superseded status.
