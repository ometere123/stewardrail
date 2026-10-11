# Studionet live evidence

The canonical current record is
[`deploy/proofs/canonical-2026-10-11-appeal-safety.json`](../deploy/proofs/canonical-2026-10-11-appeal-safety.json).
It points to the addresses in
[`deploy/deployments.json`](../deploy/deployments.json) and the six exact source
hashes in `contracts/SOURCE_MANIFEST.json`.

The packet contains finalized deployment and threshold-binding receipts and
exact decoded source hashes for the fresh stack. The corrected-stack semantic
and payment lifecycle, substantive refusal, application reversal, bonded
challenge settlement, and technical recovery are not claimed on this source
generation; older lifecycle packets are superseded.

The validator network does not expose a safe control for deliberately dropping
one internal child, so the lost-acknowledgment branch is not represented as a
forced live observation. Earlier packets are retained for audit history and
are explicitly marked `historical-superseded`.
