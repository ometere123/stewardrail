# StewardRail

**Neutral spending authority for shared AI treasuries.**

StewardRail lets several principals fund one autonomous agent without asking any one principal, the agent, or the payee to be the final judge of ambiguous spending. Deterministic limits execute synchronously. Semantic mandate compliance is decided by GenLayer validators from a frozen mandate version and independently fetched, issuer-attested evidence. Funds move only after the application appeal window is terminal and the GenLayer transaction itself is finalized.

## Why this needs GenLayer

A single wallet owner can often replace an AI jury with a human approval button. StewardRail is designed for the harder case: **money jointly governed by several principals with conflicting incentives, paid to external parties, from evidence no participant should be trusted to interpret alone**.

No single principal can override an adjudicated spend. Existing spends are pinned to the exact mandate version in force when they were requested. Evidence is not accepted merely because bytes hash correctly: every evidence item must also be attested on-chain by a wallet authorized for its role in that mandate version. Validators then re-fetch the artifact themselves, verify the digest, and independently answer the same narrow semantic question.

This creates three independent trust layers:

1. **Charter governance** — multiple principals approve mandate versions.
2. **Issuer provenance** — named issuer wallets attest the exact evidence URI + digest + role.
3. **Neutral adjudication** — GenLayer validators decide meaning from independently retrieved evidence.

## Architecture

```text
 principals (m-of-n)
       |
       v
+-------------------+       issuer wallets
| StewardCharter    |             |
| versioned mandate |             v
+---------+---------+      +-------------------+
          |                | EvidenceRegistry  |
          |                | signed attestations|
          v                +---------+---------+
+-------------------+                |
| StewardGuard      |<---------------+
| deterministic gate|
| + validator jury  |
+---------+---------+
          |
          v
+-------------------+
| StewardCourt      |
| app-level appeal  |
| fresh re-decision |
+---------+---------+
          |
          v
+-------------------+
| StewardVault      |
| GEN custody       |
| terminal payout   |
+-------------------+
```

### Contract responsibilities

| Contract | Responsibility | Cannot do |
| --- | --- | --- |
| `steward_charter.py` | m-of-n principals, immutable historical mandate versions | move treasury funds; adjudicate spends |
| `evidence_registry.py` | bind issuer wallet → charter → role → URI → digest | judge evidence meaning |
| `steward_guard.py` | synchronous deterministic screening + semantic jury | hold GEN; amend mandates; override verdicts |
| `steward_court.py` | one explicit application-level appeal with reversal semantics | pay funds; rewrite original record |
| `steward_vault.py` | hold GEN and pay only terminal effective ALLOW decisions | adjudicate; bypass appeal/finality windows |

## Design goals

### GenLayer fit

StewardRail's primary deployment is a jointly funded agent treasury. An ambiguous spend can benefit the agent, vendor, one principal, or another principal differently. No single participant is a neutral authority. A deterministic threshold engine cannot decide whether a delivered service actually satisfies the frozen shared mandate, while a conventional human approval re-centralizes the exact trust problem. GenLayer consensus is therefore at the consequence boundary: a validator verdict can authorize or withhold treasury value.

### Contract quality

The contracts are deliberately separated by authority rather than file size:

- historical mandate versions are immutable once activated;
- every spend pins its mandate version before adjudication;
- deterministic rejection happens before any model call;
- semantic cases require role-complete issuer attestations;
- leader and validators independently fetch and hash each artifact;
- validators re-answer the same question rather than grading leader prose;
- application appeals can **reverse** either direction and are tested as state transitions;
- the vault reads the court's effective terminal decision and pays exact recipient + exact amount once;
- no single principal override exists for an adjudicated historical spend.

### Engineering quality

There is **one source representation per deployable contract**. `contracts/*.py` is both the human-readable source and the deployment source. CI rejects drift in `contracts/SOURCE_MANIFEST.json`, runs deterministic model tests, contract structure/adversarial tests, mutation checks, frontend type/build tests, and source-reference checks. The frontend never reimplements mandate classification; it calls `preview_spend` on the guard.

## Network lock

This repository is locked to stable Studionet:

- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com`
- CLI: repository-local `genlayer@0.39.1`

Do not silently switch networks.

## Frontend

Next.js App Router, injected EIP-1193 wallet only. No WalletConnect, Reown, Privy, embedded wallet, backend authority, API route, database, cron, queue, or centralized adjudicator.

Routes:

- `/` — product and trust model
- `/workspace` — shared treasury overview
- `/charters/new` — create the m-of-n charter
- `/charters/[address]` — mandate versions and principals
- `/spends/new` — guard preview then request
- `/spends/[id]` — evidence, jury result, appeal state, payout state
- `/evidence` — issuer attestation console
- `/court` — open and resolve application appeals
- `/vault` — fund, inspect, and settle treasury
- `/verify` — source/address verification
- `/docs` — reviewer-oriented architecture and threat model

Every signing surface hard-blocks the wrong network and displays the exact action, contract, value, and chain before the wallet prompt. Submitted transactions are tracked by their existing hash; the UI never treats `ACCEPTED` alone as application success.

## Repository layout

```text
contracts/               exact deployable Intelligent Contract sources
reference/               pure deterministic policy/appeal model
frontend/                Next.js App Router dapp
scripts/                 manifest, preflight, mutation and repository checks
tests/unit/              deterministic model tests
tests/direct/            exact-source in-memory adversarial harness
deploy/                  61999 deploy + lifecycle scripts and evidence schema
docs/                    architecture, threat model, live proof plan, reviewer packet
STEWARDRAIL_CODEX_MASTER_HANDOFF.txt  completion/deployment instructions
```

## Local verification

```bash
python3 scripts/update_source_manifest.py --check
python3 scripts/preflight.py
python3 -m pytest -q
python3 tests/mutation_check.py

# Exact contract-source harness above runs in ordinary pytest.
# GenVM lint uses the pinned stable linter.
genvm-lint check contracts/steward_charter.py
genvm-lint check contracts/evidence_registry.py
genvm-lint check contracts/steward_guard.py
genvm-lint check contracts/steward_court.py
genvm-lint check contracts/steward_vault.py

cd frontend
npm install
npm run typecheck
npm run test
npm run build
```

## Live proof required before submission

Repository structure alone is not live evidence. Before submission, run and preserve a fresh Studionet lifecycle proving:

1. two of three principals activate a mandate;
2. an authorized issuer attests an evidence digest;
3. deterministic refusal needs no jury;
4. semantic ALLOW from independently fetched attested evidence;
5. semantic REFUSE from missing/invalid role provenance;
6. ALLOW → appeal REFUSE appeal blocks payout;
7. REFUSE → appeal ALLOW appeal becomes payable only after the appeal/finality gates;
8. wrong issuer, digest mismatch, prompt injection, duplicate payout, early payout, stale mandate mutation and wrong-network writes all fail;
9. every relevant GenLayer transaction is `FINALIZED`, validator consensus agrees, and execution succeeded.

The scripts in `deploy/` are written to produce a machine-readable packet rather than relying on screenshots.

## License

MIT.
