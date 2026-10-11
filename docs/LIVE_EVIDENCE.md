# Studionet live evidence

The canonical current record is
[`deploy/proofs/final-remediation-2026-10-11.json`](../deploy/proofs/final-remediation-2026-10-11.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment and threshold-binding receipts, the
active two-principal mandate, exact source hashes, issuer attestations, and a
semantic `ALLOW` lifecycle through Court → Guard → BondVault → Vault. It records
a finalized 1 GEN treasury funding, a 1 GEN standing deposit, and a funded
1 GEN payout with a finalized payable child and an independently observed
recipient balance increase. The duplicate payment attempt finalized with the
expected error and no balance movement. Substantive refusal, application
reversal, bonded challenge settlement, and technical recovery are not claimed
on this source generation.

The validator network does not expose a safe control for deliberately dropping
one internal child, so the lost-acknowledgment branch is not represented as a
forced live observation. Earlier packets are retained for audit history and
are explicitly marked `historical-superseded`.
