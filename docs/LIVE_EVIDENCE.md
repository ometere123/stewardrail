# Studionet live evidence

The canonical current record is
[`deploy/proofs/canonical-2026-10-11-appeal-safety.json`](../deploy/proofs/canonical-2026-10-11-appeal-safety.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment receipts, threshold-approved mandate
v2, exact decoded source hashes, a semantic ALLOW through Court → Guard → Vault,
an upheld bonded challenge with settlement and repeated reconciliation, a
funded 1 GEN payout with an independently credited child transfer, a
technical-unresolved case closed after its bounded retry limit, a substantive
ALLOW→REFUSE reversal, and a substantive REFUSE→ALLOW reversal. Each reversal
has its finalized Court, Guard and Vault descendants recorded in the packet.

The validator network does not expose a safe control for deliberately dropping
one internal child, so the lost-acknowledgment branch is not represented as a
forced live observation. Earlier packets are retained for audit history and
are explicitly marked `historical-superseded`.
