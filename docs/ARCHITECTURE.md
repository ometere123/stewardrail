# StewardRail architecture

## 1. Consequence boundary

StewardRail is not a monitoring dashboard. The value-moving path is:

```text
agent -> StewardGuard -> finalized primary -> StewardCourt
      -> app appeal or expiry -> finalized semantic terminal -> StewardGuard
      -> finalized economic authorization -> StewardVault -> recipient
```

The vault has no method that asks the agent or any one principal whether a spend should be paid. Court never authorizes custody directly. A payment is possible only after Guard completes deterministic terminal checks and sends the exact economic decision to Vault from a **GenLayer finalized message**.

## 2. Why the governance model matters

The charter represents a shared treasury. At least two principals exist and the threshold is at least two. A mandate version activates only when the threshold approves identical canonical JSON. Historical versions are immutable and every spend pins the version active at request time.

This removes the single-principal escape hatch that makes neutral consensus optional in ordinary agent-wallet policy engines.

## 3. Evidence provenance

A hash alone only proves that every validator received the same bytes. StewardRail adds three checks before semantic content is trusted:

1. the frozen mandate version authorizes a specific issuer wallet for a role;
2. the issuer wallet has made an on-chain attestation for the exact charter, role, URI and SHA-256 digest;
3. the URI origin is explicitly allowed for that issuer in the frozen mandate.

The registry never overwrites an evidence identity. Revocation adds a timestamp instead. `status_at` therefore preserves whether an attestation was valid at the spend request timestamp.

During adjudication the leader and validators independently fetch every URI and recompute the SHA-256. Content is bounded and wrapped as untrusted evidence. Prompt injection inside an invoice or delivery report is explicitly non-authoritative.

## 4. Deterministic first, semantics only when needed

`StewardGuard.request_spend` enforces synchronously:

- positive amount;
- per-spend cap;
- rolling authorization exposure;
- category allowlist;
- recipient denylist.

A semantic rule has one trigger: `always`, `amount_gte`, or `category_in`. Only fired rules are sent to the jury. If no semantic trigger fires, the guard records `allow` immediately. If a deterministic rule fails, it records `refuse` immediately. Either result enters the same finalized court path, so deterministic allows cannot bypass the application appeal window.

## 5. Semantic consensus

For held spends, every required evidence role must be present with valid frozen provenance before a model call occurs. Missing provenance fails closed without spending validator compute.

For the actual semantic question, leader and validators independently:

- fetch the same pinned evidence;
- verify each digest;
- answer the same narrow rule question;
- compare the resulting `allow|refuse` verdict.

An `allow` below the confidence floor is rejected explicitly as an unsafe semantic result. It is never silently rewritten to `refuse`; the transaction fails closed and the spend remains without a new semantic decision.

## 6. Appeal reversal

The application appeal is intentionally not just a challenge flag. The appeal panel re-runs the semantic decision over the frozen mandate and evidence. Its output becomes the effective decision regardless of direction:

- primary `allow` -> appeal `refuse` blocks payout;
- primary `refuse` -> appeal `allow` becomes payable;
- same-direction results affirm.

One application appeal is allowed. The appeal transaction sends the effective semantic result only to Guard through `emit(on="finalized")`. Guard validates historical evidence, replay policy, exposure, and Vault bindings before emitting the economic result to Vault through a second `emit(on="finalized")`. An unappealed case is closed by `close_unappealed`, which uses the same two-stage delivery. Reconciliation re-emits the stored Court result through Guard without changing it.

## 7. Protocol finality invariant

The vault does **not** infer finality from timestamps or from an `ACCEPTED` receipt. It only accepts `record_terminal` from the bound Guard, and verifies the Guard/Court/Charter binding. Court cannot call Vault directly. Consequently, a primary or appeal state that is still protocol-appealable cannot become a vault terminal record, and a Guard deterministic downgrade becomes an explicit terminal refusal rather than a stuck child transaction.

The frontend also reads accounting state with `LATEST_FINAL` where supported and reports consensus status and execution result separately.

## 8. Frozen enforcement consequences

Each semantic rule may carry a mandate-approved consequence: `observe`, `refuse`, `freeze`, `revoke`, or `clawback`. Charter validates this enum before a version can activate. Observe-only rules still run through semantic adjudication and are recorded as an observed breach without refusing the spend solely because of that rule. A refusal-level result is an economic refusal. Freeze-level and stronger results set Guard's frozen state before new agent requests are considered.

Unfreezing is not an owner operation. Principals approve an exact `(guard, freeze_epoch, nonce)` action through Charter, and Guard consumes that approval once. Replays and single-principal attempts fail.

Guard also supports optional recipient-scoped rolling limits. The aggregation key is the canonical recipient address stored in the spend, never an agent-provided group identifier. Global and recipient exposure are evaluated from the same request-time ledger and preserve unresolved semantic reservations.

## 9. Custody and recovery

The vault pays an exact recipient and exact amount once. A terminal refusal is never payable. No agent withdrawal exists. Treasury recovery is available only after the charter threshold approves the exact vault, destination, amount and recovery nonce.

## 10. Deployment order

1. `StewardCharter`
2. `EvidenceRegistry`
3. `StewardCourt(charter, registry)`
4. `StewardGuard(charter, registry, court)`
5. `StewardVault(charter, guard, court)`

This order avoids circular mutable configuration. The court accepts primary decisions only from guards that self-report the same charter, registry and court. The vault is immutable-bound to one guard and one court.

## 11. No generated deployable copy

There is no `contracts/build`, minifier, code generator, or bundled contract copy. `contracts/*.py` is the readable source and the exact deployment input. `contracts/SOURCE_MANIFEST.json` records SHA-256 and byte size for those exact files. CI regenerates the manifest in check mode and fails on drift.
