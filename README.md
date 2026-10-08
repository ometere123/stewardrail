# StewardRail

**Neutral spending authority for shared AI treasuries.**

StewardRail lets several principals fund one autonomous agent without asking any one principal, the agent, or the payee to be the final judge of ambiguous spending. Deterministic limits execute synchronously. Semantic mandate compliance is decided by GenLayer validators from a frozen mandate version and independently fetched, issuer-attested evidence. Funds move only after the application appeal window is terminal and the Court → Guard → Vault message chain has finalized successfully.

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
 | effective result  |
 +---------+---------+
           | finalized
           v
 +-------------------+
 | StewardGuard      |
 | terminal economic |
 | authorization     |
 +---------+---------+
           | finalized
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
| `steward_vault.py` | hold GEN and pay only Guard-delivered terminal economic ALLOW decisions | adjudicate; accept direct Court authority |

## Protocol boundaries

StewardRail's primary deployment is a jointly funded agent treasury. An ambiguous spend can benefit the agent, vendor, one principal, or another principal differently. No single participant is a neutral authority. A deterministic threshold engine cannot decide whether a delivered service actually satisfies the frozen shared mandate, while a conventional human approval re-centralizes the exact trust problem. GenLayer consensus is therefore at the consequence boundary: a validator verdict can authorize or withhold treasury value.

### Contract boundaries

The contracts are deliberately separated by authority rather than file size:

- historical mandate versions are immutable once activated;
- every spend pins its mandate version before adjudication;
- deterministic rejection happens before any model call;
- semantic cases require role-complete issuer attestations;
- leader and validators independently fetch and hash each artifact;
- validators re-answer the same question rather than grading leader prose;
- application appeals can **reverse** either direction and are tested as state transitions;
- Court sends only a finalized semantic result to Guard; Guard's terminal economic record is the only custody authority and fixes recipient + amount;
- no single principal override exists for an adjudicated historical spend.

Semantic rules may also freeze the agent or revoke eligible unpaid prior authorizations. `observe` consequences record an observed breach without making that rule an economic refusal. A freeze blocks new agent requests until principals approve the exact Guard, freeze epoch, and nonce through Charter. A severe terminal result can mark earlier unpaid ALLOW records revoked; Vault checks the Guard's finalized revocation state before paying, while already-paid history remains unchanged.

An optional `recipient_rolling` policy aggregates exposure by the canonical recipient address stored in each spend. The agent cannot provide an alternate grouping key to evade that limit.

### Reproducibility

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
- `/docs` — protocol documentation and verification links

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
docs/                    architecture, threat model, live proof plan and deployment notes
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

## Live deployment verification

Repository structure alone is not live evidence. A canonical Studionet deployment should be accompanied by a machine-readable lifecycle record proving:

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

## Canonical deployment

| Contract | Studionet address |
| --- | --- |
| StewardCharter | [0xd42FFa9Fb7fbecc151FFa38408B764c34471b225](https://explorer-studio.genlayer.com/address/0xd42FFa9Fb7fbecc151FFa38408B764c34471b225) |
| EvidenceRegistry | [0x40E54913Ad12e70531De905415E4B9a5D44B8760](https://explorer-studio.genlayer.com/address/0x40E54913Ad12e70531De905415E4B9a5D44B8760) |
| StewardCourt | [0x0F2DA1BeA53833EAbBe6842DCB185DB50A0bF32f](https://explorer-studio.genlayer.com/address/0x0F2DA1BeA53833EAbBe6842DCB185DB50A0bF32f) |
| StewardBondVault | [0x6781e714D2b11647EB225b74223F715a4F090ccf](https://explorer-studio.genlayer.com/address/0x6781e714D2b11647EB225b74223F715a4F090ccf) |
| StewardGuard | [0x0257850837f4e4AEB978c851144D4744a8A46524](https://explorer-studio.genlayer.com/address/0x0257850837f4e4AEB978c851144D4744a8A46524) |
| StewardVault | [0x936EfE417E0CCC020D425D9440a924d2994Bd9E1](https://explorer-studio.genlayer.com/address/0x936EfE417E0CCC020D425D9440a924d2994Bd9E1) |

Network: Studionet · Chain ID 61999 · RPC `https://studio.genlayer.com/api` · CLI `0.39.1`.

Deployment transactions and source hashes are recorded in [`deploy/deployments.json`](deploy/deployments.json) and [`contracts/SOURCE_MANIFEST.json`](contracts/SOURCE_MANIFEST.json). The expanded deployment record is [`deploy/proofs/expanded-deployment.json`](deploy/proofs/expanded-deployment.json).

The six deployed source hashes are:

```text
steward_charter.py  726f5a19f5cd66987ed3d568be1c8b6e593801f8e9252b1e78a5f49fa2a37f2d
evidence_registry.py f7bf6547440f954c18acb191fd211307d6cdecf953d3faceaa7946d8f5d831dd
steward_court.py    30f6bf7284c6efab21d44db4d3d5fc44ccd932a8a8594db52a5c37a33c76d6a8
steward_bond_vault.py 680b837bbf5258bc11caa3b4c799a0d91856044d200b116e260b68b3af3c22a9
steward_guard.py    34673c66bdcc6bd037cbbdaafac1b2f121bd81a1d421051272292708f67e63ee
steward_vault.py    685347698db01fa0dd282dee4e3b836fd792c3d4d20bb30757749975f7f656d6
```

## Observed live scenarios

The expanded deployment packet records six finalized deployments and threshold collateral binding. Economic lifecycle evidence remains separate and is only claimed when a corresponding proof row exists.

Fresh funded payout, duplicate-payout rejection, and threshold-recovery transactions are not present in the packet and are intentionally not claimed here.

## Verification

```bash
python -m pytest -q
python tests/mutation_check.py
python scripts/direct_mode.py
bash scripts/genvm_lint.sh
python scripts/update_source_manifest.py --check
python scripts/preflight.py

cd frontend
npm ci
npm run test
npm run typecheck
npm run build
```

The current local results are 47 Python tests passed with 6 skipped, 6 official Direct Mode tests passed, 25 of 25 source mutants killed, all five contract lint checks passed, and frontend test/typecheck/build passed.

## License

MIT.
