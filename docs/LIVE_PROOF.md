# Live proof index

The current machine-readable packet is
[`deploy/proofs/final-release-2026-10-10.json`](../deploy/proofs/final-release-2026-10-10.json).

It records the source-matched six-contract Studionet stack, source hashes,
deployment and binding transactions, and a funded semantic `ALLOW` lifecycle.
Spend `1` finalized through Court → Guard → BondVault lock/confirmation →
Vault, was funded with 20 GEN, paid 1 GEN, and produced a finalized
`value_credited` transfer child. Spend `3` registered and resolved a bonded
challenge, finalized through Guard, Vault and BondVault, and returned its 0.05
GEN bond once. Two finalized reconciliation calls then completed without a
payable child; the packet records unchanged physical balances and the final
`delivered` state. The replay-safe settlement behavior is also covered by the
direct adversarial suite for duplicate payable credits and simultaneous retries.
Historical packets remain in `deploy/proofs/` with explicit superseded status.
