# Studionet 61999 live proof plan

The final submission should not claim completion until this packet exists from a fresh deployment.

## Network gate

- `npx genlayer@0.39.1 network set studionet`
- `npx genlayer@0.39.1 network info`
- independently confirm RPC `https://studio.genlayer.com/api`
- independently confirm chain id `61999` / `0xF22F`
- abort if any command resolves to a chain other than 61999

## Required lifecycle

1. Deploy the five exact source files in `contracts/` and record source SHA-256 plus deployment transaction.
2. Two of three principals approve the exact same initial mandate and activate version 1.
3. An authorized issuer wallet attests an evidence URI+digest.
4. Agent requests a deterministic refusal and prove no nondeterministic adjudication call was needed.
5. Agent requests a semantic spend, attaches role-complete authenticated evidence, and adjudicates.
6. Prove leader/validators re-fetch digest-bound evidence and the primary decision reaches court only after the guard adjudication transaction is FINALIZED.
7. **ALLOW -> appeal -> REFUSE:** appeal within the window, prove vault has no terminal allow before appeal finalization, then prove terminal refusal blocks `pay`.
8. Fresh case: **REFUSE -> appeal -> ALLOW:** prove reversal, wait for the appeal transaction to FINALIZE, prove the finalized court message creates a vault terminal allow, then pay exactly once.
9. Unappealed ALLOW: wait for application window, call `close_unappealed`, wait for FINALIZED, then pay.
10. Threshold recovery: one approval fails, threshold approvals succeed, exact nonce prevents replay.

## Adversarial cases

- wrong issuer wallet;
- correct issuer but wrong role;
- correct wallet/role but disallowed URI origin;
- `vendor.example.evil.tld` origin confusion;
- evidence attested only after spend request;
- evidence revoked before spend request;
- digest mismatch;
- unavailable evidence URI;
- prompt injection asking validators to ignore the mandate;
- malformed model output;
- low-confidence allow;
- duplicate primary finalized message;
- conflicting primary message;
- duplicate terminal message;
- conflicting terminal message;
- duplicate payout;
- wrong vault passed to court;
- non-participant appeal;
- appeal after deadline;
- wrong-network frontend write;
- user wallet rejects signature;
- page refresh while transaction is processing;
- ACCEPTED + execution error must display failure, not success.

## Proof packet fields

Each transaction row should contain:

- scenario id;
- contract and method;
- transaction hash;
- status name;
- execution result;
- consensus/decision identity if available;
- finalized timestamp;
- relevant before/after state;
- explorer URL;
- source SHA-256 set;
- frontend commit SHA.

Keep machine-readable JSON under `deploy/proofs/` and a concise `docs/LIVE_EVIDENCE.md` index. Do not replace transaction evidence with screenshots.
