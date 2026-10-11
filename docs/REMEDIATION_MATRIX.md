# Remediation matrix

This matrix ties the requested safety properties to the source, local checks, and
the current canonical proof packet.  `NOT OBSERVED` means the property is tested
locally but was not rerun on the fresh Studionet stack; it is not a claim of live
success.

| Requirement | Source / test evidence | Current live status |
| --- | --- | --- |
| Evidence retrieval failure is not substantive refusal | `contracts/steward_guard.py`, `contracts/steward_court.py` technical classifications; `tests/direct/test_economic_lifecycle.py` technical recovery tests | OBSERVED for spend 8: integrity error, bounded retries, no economic authorization |
| Unresolved technical case closes neutrally and releases exposure | `StewardCourt.reconcile_terminal`, `StewardGuard.close_technical`; direct regression and live spend 8 | OBSERVED: `0x21b26f29…` → `0x96b795d9…` |
| Primary, appeal and challenge confidence floors | Guard/Court `_same_verdict` helpers and confidence-boundary tests in `tests/direct` | Local tests PASS |
| Exact rolling-window boundaries and release semantics | indexed Guard exposure queues; `tests/unit/test_high_volume_rolling.py` (100, 1,000, 5,000 records) | Local reference PASS |
| Court → Guard → BondVault → Vault authority | six bound sources; sender and binding assertions in direct suites | OBSERVED for spend 6; all children FINALIZED/SUCCESS |
| One-shot settlement and replay protection | BondVault settlement-delivery state, Vault duplicate-credit guards, mutation suite | OBSERVED: challenge 1 settled; two reconciliations created no payable child |
| Independent authenticated issuer roles | Charter issuer policies and Registry historical attestation checks | OBSERVED for spend 6/7: vendor and delivery roles are distinct wallets |
| Source parity | base64-decoded `gen_getContractCode` SHA-256 equals `SOURCE_MANIFEST.json` for all six addresses | PASS |
| Exact source and runtime gates | pytest, mutation, Direct Mode, six-contract lint, manifest, preflight, frontend checks | PASS locally |
| Production bindings | `frontend/.env.local` and Vercel Production public variables | PASS: `dpl_9ZNyaPsFYJ14K6RAV43aqoEWfT8A`; `/verify` reads all six current addresses and bindings on Studionet 61999 |
| Funded payout and balance conservation | packet spend 7 payout readback and payment child | OBSERVED: recipient +1 GEN, Vault treasury −1 GEN; duplicate rejected |

Historical lifecycle packets remain in `deploy/proofs/` for audit context only and
are not evidence for the corrected source generation.
