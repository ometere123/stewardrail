# Remediation matrix

This matrix ties the requested safety properties to the source, local checks, and
the current canonical proof packet.  `NOT OBSERVED` means the property is tested
locally but was not rerun on the fresh Studionet stack; it is not a claim of live
success.

| Requirement | Source / test evidence | Current live status |
| --- | --- | --- |
| Evidence retrieval failure is not substantive refusal | `contracts/steward_court.py` technical classifications; `tests/direct/test_economic_lifecycle.py::test_appeal_digest_failure_closes_neutral_without_calling_primary_technical_close` | NOT OBSERVED on fresh stack |
| Unresolved appeal closes neutrally and releases exposure | `StewardCourt.close_unappealed`, `StewardGuard.close_appeal_technical`; direct regression above | NOT OBSERVED on fresh stack |
| Primary, appeal and challenge confidence floors | Guard/Court `_same_verdict` helpers and confidence-boundary tests in `tests/direct` | Local tests PASS |
| Exact rolling-window boundaries and release semantics | indexed Guard exposure queues; `tests/unit/test_high_volume_rolling.py` (100, 1,000, 5,000 records) | Local reference PASS |
| Court → Guard → BondVault → Vault authority | six bound sources; sender and binding assertions in direct suites | Bindings FINALIZED; economic lifecycle NOT OBSERVED on fresh stack |
| One-shot settlement and replay protection | BondVault settlement-delivery state, Vault duplicate-credit guards, mutation suite | Local adversarial PASS; fresh live settlement NOT OBSERVED |
| Independent authenticated issuer roles | Charter issuer policies and Registry historical attestation checks | Fresh deployment bindings verified; attestation lifecycle NOT OBSERVED |
| Source parity | base64-decoded `gen_getContractCode` SHA-256 equals `SOURCE_MANIFEST.json` for all six addresses | PASS |
| Exact source and runtime gates | pytest, mutation, Direct Mode, six-contract lint, manifest, preflight, frontend checks | PASS locally |
| Production bindings | `frontend/.env.local` updated to fresh addresses; Vercel env update pending | NOT OBSERVED after fresh deployment |
| Funded payout and balance conservation | existing historical packets are explicitly superseded | NOT OBSERVED on corrected stack |

Historical lifecycle packets remain in `deploy/proofs/` for audit context only and
are not evidence for the corrected source generation.
