# Live proof index

The current machine-readable packet is
[`deploy/proofs/replay-safe-final-stack-2026-10-10.json`](../deploy/proofs/replay-safe-final-stack-2026-10-10.json).

It records the source-matched six-contract Studionet stack, source hashes,
deployment and binding transactions, and a funded semantic `ALLOW` lifecycle.
Spend `1` finalized through Court → Guard → BondVault lock/confirmation →
Vault, was funded with 2 GEN, paid 0.1 GEN, and produced a finalized
`value_credited` transfer child. The replay-safe settlement behavior is covered
by direct adversarial tests for both settlement directions, duplicate payable
credits, simultaneous retries and receiver-side conservation. A fresh live
bonded settlement was not observed because its challenge window elapsed; no
older packet is presented as current proof.
Historical packets remain in `deploy/proofs/` with explicit superseded status.
