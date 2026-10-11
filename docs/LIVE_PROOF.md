# Live proof index

The current machine-readable packet is
[`deploy/proofs/canonical-2026-10-11-appeal-safety.json`](../deploy/proofs/canonical-2026-10-11-appeal-safety.json).

It records the source-matched six-contract Studionet stack, source hashes,
deployment and mandate transactions, a Court → Guard → Vault ALLOW, an upheld
bonded challenge and two idempotent reconciliations, a 1 GEN payout with exact
recipient and treasury deltas, and bounded technical-unresolved recovery.
Native EOA transfer children are evidenced by `value_credited` and independent
balance deltas; their consensus label is not treated as execution success.
Fresh application reversals in both directions and substantive semantic REFUSE
are recorded with finalized descendants in the current packet.
Historical packets remain in `deploy/proofs/` with explicit superseded status.
