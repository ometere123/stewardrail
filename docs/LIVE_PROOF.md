# Live proof index

The canonical fresh packet is
[`deploy/proofs/final-fresh-studionet-2026-10-10.json`](../deploy/proofs/final-fresh-studionet-2026-10-10.json).
It records the six-contract Studionet deployment, threshold binding, authenticated
evidence, Court → Guard → Vault terminal delivery, challenge settlement,
reconciliation, payout observation and threshold recovery.

The packet distinguishes `FINALIZED` protocol execution from EOA value-transfer
delivery. The observed payout and recovery children reported `value_credited=true`
and `NO_MAJORITY`, so those transfers are not described as consensus-confirmed.
Scenarios not listed as observed in the packet remain unclaimed. Earlier packets
are retained with an explicit `historical-superseded` status.
