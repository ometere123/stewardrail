# StewardRail threat model

| ID | Threat | Control | Residual risk |
| --- | --- | --- | --- |
| T1 | Agent exceeds hard limits | synchronous guard classification | conservative rolling exposure can temporarily throttle after refused requests |
| T2 | One principal rewrites policy after a request | threshold activation + immutable historical versions + spend version pin | principals can activate a new version for future spends |
| T3 | Fabricated evidence with a correct hash | frozen authorized issuer wallet + on-chain attestation + allowed HTTPS origin | authorized issuer can still attest false content |
| T4 | Evidence changes after commitment | independent validator SHA-256 recomputation | source can become unavailable; system fails closed |
| T5 | Prompt injection inside evidence | evidence explicitly marked untrusted; bounded content; validators answer same fixed question | model robustness is probabilistic; neutral consensus reduces but does not eliminate model error |
| T6 | Leader lies about semantic result | validators independently re-fetch and re-answer | committee majority can still be wrong |
| T7 | Single principal overrides jury | no per-spend override method exists | threshold governance can approve future policy, not historical result |
| T8 | Appeal is cosmetic | appeal effective verdict directly replaces primary in terminal message | one application appeal only |
| T9 | ALLOW paid before reversal/finality | court-to-vault terminal message executes only on finalized parent | correctness depends on GenLayer finalized-message semantics |
| T10 | Duplicate finalized messages | court and vault terminal records are idempotent and conflict-rejecting | conflicting protocol bug would fail closed |
| T11 | Duplicate payout | vault `paid` flag set before transfer | recipient contract behavior is outside StewardRail |
| T12 | Treasury recovery bypass | exact threshold-approved recovery tuple + monotonic nonce | principals controlling threshold can recover funds by design |
| T13 | Wrong network signing | frontend checks chain id 61999 before every write; deployment preflight checks network | user can bypass repo tooling manually |
| T14 | Frontend claims accepted tx succeeded | waits for decision/finalization and checks execution outcome | gateway/API incompatibility must be surfaced as unknown, never assumed success |
| T15 | Readable/generated contract drift | no second deployable representation exists | deployment operator can still choose a different file outside repo; proof packet records hashes |
| T16 | Observe rule silently blocks spending | consequence is frozen in the mandate and Guard records `enforcement=observe` while preserving the semantic case | observe-only policy does not provide economic protection by itself |
| T17 | Severe semantic breach leaves the agent able to continue requesting | Guard freezes agent requests at terminal enforcement and exposes epoch/reason | a threshold must explicitly approve unfreeze |
| T18 | One principal lifts a freeze or replays an unfreeze | Charter thresholds an exact guard/epoch/nonce action; Guard consumes nonce once | threshold principals can intentionally unfreeze by design |
| T19 | Spend splitting evades a recipient limit | optional recipient rolling exposure derives its key from the canonical recipient address | limits must be configured in the frozen mandate |

## Evidence authenticity boundary

StewardRail authenticates **who attested** an artifact, not whether the issuer is honest. The mandate's principals decide which issuer wallets and HTTPS origins are authoritative for each role. This is an explicit governance choice and is reviewable in the frozen mandate version.

## Neutrality boundary

The product is designed for multiple principals. If one entity controls the charter threshold, issuer keys, and appeal participants, the deployment has re-centralized itself even though the contracts remain correct.
