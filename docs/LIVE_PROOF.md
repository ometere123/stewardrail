# Live proof index

The current machine-readable packet is
[`deploy/proofs/final-remediation-2026-10-11.json`](../deploy/proofs/final-remediation-2026-10-11.json).

It records the source-matched six-contract Studionet stack, source hashes,
deployment and binding transactions, issuer attestations, and a finalized
semantic `ALLOW` lifecycle through Court → Guard → BondVault → Vault. A 1 GEN
funded payout is observed: its payable child finalized with value credited, the
recipient balance increased by exactly 1 GEN, and a duplicate payment finalized
with the expected execution error without moving balances. The packet also
records the correct standing-coverage economic refusal for a separate spend.
Substantive refusal, reversal, challenge settlement, and technical recovery
remain explicitly unobserved on this source generation. The replay-safe
settlement behavior is covered by the direct adversarial suite for duplicate
payable credits and simultaneous retries.
Historical packets remain in `deploy/proofs/` with explicit superseded status.
