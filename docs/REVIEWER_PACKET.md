# Reviewer packet

## Claim

StewardRail is neutral spending authority for a **shared** AI treasury. Multiple principals freeze the mandate, external issuer wallets authenticate evidence, GenLayer validators decide ambiguous compliance, an application appeal can reverse either direction, and a vault pays only after the terminal court result reaches it through a protocol-finalized message.

## Why Fit 5 is the target

The primary use case removes the ordinary fallback of “the owner can just approve it manually.” There is no single owner. The governed money belongs to a threshold charter with participants that may have conflicting incentives. Neutral semantic consensus is therefore the authority boundary for ambiguous spending.

## Why Contract 5 is the target

Five contracts separate five authorities: policy governance, evidence provenance, spend screening/adjudication, appeal, and custody. No contract can silently take over another role. Historical policy and evidence validity are time-pinned. The appeal actually changes the effective decision. The vault receives terminal authorization only from the court's finalized message.

## Why Engineering 5 is the target

- one deployable source representation;
- source hashes checked in CI;
- deterministic model tests;
- structural/adversarial contract invariants;
- mutation battery;
- 61999 network hard gate;
- Next.js App Router frontend with injected EIP-1193 only;
- wrong-network hard block;
- transaction drawer that distinguishes processing, decided, finalized and execution failure;
- machine-readable live proof plan.

## Claims intentionally deferred until live proof exists

The repository does **not** claim that a fresh Studionet appeal reversal has already been observed. The required proof is listed in `docs/LIVE_TEST_PLAN.md` and the completion handoff forbids submission before it is produced.
