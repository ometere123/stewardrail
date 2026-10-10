# StewardRail

StewardRail is shared treasury control for autonomous agents: multiple principals approve a mandate, authorized issuers attest external evidence, GenLayer validators resolve bounded semantic questions, deterministic policy enforces the economic result, and finalized custody executes the exact payment.

## What StewardRail is

Shared treasury operations contain two different kinds of decisions. A spend cap, recipient allowlist, or rolling exposure limit can be evaluated exactly. Whether an authenticated deliverable satisfies a jointly approved brief requires interpretation. StewardRail keeps those layers separate instead of giving one wallet authority over both.

For example, “spend no more than 1 GEN” is deterministic, while “does this vendor deliverable satisfy the approved brief?” is a bounded semantic question. The agent can submit a request, but it cannot rewrite the mandate, choose the semantic verdict, or withdraw treasury value.

## Core trust model

- **Principals** approve identical canonical mandate data. A mandate version becomes active only at its configured threshold and is immutable thereafter.
- **Agent** submits spend requests and evidence. It cannot activate a mandate alone, override a semantic result, or withdraw the treasury.
- **Evidence issuers** attest a specific role, URI, and SHA-256 digest. Issuer authorization and historical validity are checked by the registry.
- **StewardCharter** stores principals, thresholds, mandate versions, and threshold-governed recovery actions.
- **EvidenceRegistry** records and validates issuer attestations, including historical status.
- **StewardGuard** applies deterministic policy, checks evidence and exposure, starts semantic adjudication, and creates the final economic authorization.
- **StewardCourt** records the primary semantic result and application appeals. It does not custody or pay funds.
- **StewardVault** holds treasury value and accepts terminal economic decisions only from the configured Guard.
- **StewardBondVault** holds agent standing and challenge bonds. It settles finalized challenge outcomes without adjudicating semantics.

No individual principal has a per-spend semantic override. An agent cannot withdraw custody. Court cannot bypass Guard, and Vault does not adjudicate. An appeal statement is an argument, not authenticated evidence.

## Architecture

```text
Principals
    │ threshold approval
    ▼
StewardCharter ── immutable mandate versions
    │
Evidence issuer ──► EvidenceRegistry
    │
Agent
    ▼
StewardGuard
    │ deterministic policy and semantic request
    ▼
StewardCourt
    │ finalized semantic result
    ▼
StewardGuard
    │ finalized economic authorization
    ▼
StewardVault ── exact payment ──► Recipient
    ▲
    │ finalized challenge settlement and standing accounting
StewardBondVault
```

The custody authority path is deliberately `Court → Guard → Vault`. A Court result is not a payment instruction until Guard has rechecked the frozen mandate, evidence, replay policy, and exposure.

## Decision lifecycle

Deterministic refusals can finish without semantic consensus. A semantic request follows:

```text
request → HELD → evidence attachment and sealing → validator adjudication
        → Court primary result → application appeal window
        → Guard terminal economic result → Vault authorization → payment
```

Readbacks distinguish the primary semantic result, Court effective result, Guard terminal economic result and reason, and Vault payment state. Unresolved semantic cases reserve rolling capacity while an appeal remains possible; terminal `ALLOW` remains counted and terminal `REFUSE` releases the reservation. Observe, refuse, freeze, revoke, and clawback consequences are frozen in the approved mandate version.

## Evidence provenance and replay

An evidence identity is bound to:

```text
charter | issuer wallet | role | URI | SHA-256 digest
```

The mandate fixes each role's allowed HTTPS origin and usage policy (`single_use` or `reusable`). Evidence must have been attested and historically valid no later than the spend request time. Fetched content is untrusted input to the semantic prompt; it cannot change protocol instructions or the required result schema.

Single-use evidence is consumed only when Guard records a terminal economic `ALLOW`. A terminal `REFUSE` does not consume it, and an identical terminal retry is idempotent. Reusable evidence may be used again when the frozen mandate permits it.

## Appeals and challenges

Each semantic case has a bounded application appeal window. The appeal uses the same frozen mandate and must satisfy all required authenticated evidence roles; a persuasive statement cannot substitute for a missing role. Court can therefore preserve or reverse the effective semantic result without becoming a custody authority.

The deployed BondVault also supports a separate bonded challenge path. A challenge quotes its bond from the spend's frozen policy, is registered through Court, and reaches Guard before any custody consequence. Historical lifecycle packets contain post-payment restitution observations for an earlier source generation; the current packet does not relabel those transactions as evidence for this corrected deployment.

## Finalized internal authority and reconciliation

Irreversible authority messages use finalized child transactions:

```text
Court finalized
    ↓ Guard child finalized
Guard finalized
    ↓ Vault child finalized
Vault custody result
```

Terminal payloads are fingerprinted and idempotent. Court reconciliation can re-emit an identical Guard payload; Guard does not consume evidence twice and can re-deliver the exact Vault authorization.

## Treasury safety

Vault records the recipient and amount from the frozen Guard spend record. `pay(spend_id)` requires a terminal economic `ALLOW`, sufficient treasury, and no prior payment; callers cannot substitute a recipient or amount. The current packet records a 1 GEN payment, a separate finalized transfer child with `value_credited: true`, and a duplicate-payment rejection in the adversarial suite. Threshold recovery remains governed by the Charter rather than an individual owner.

## Canonical Studionet deployment

The current source-matched stack is recorded in [`deploy/deployments.json`](deploy/deployments.json) and the current deployment/proof status is [`deploy/proofs/final-source-stack-2026-10-10.json`](deploy/proofs/final-source-stack-2026-10-10.json). Earlier lifecycle packets are historical records for superseded source generations.

| Contract | Studionet address |
| --- | --- |
| StewardCharter | [0x5DAF…f0c6](https://explorer-studio.genlayer.com/address/0x5DAF7d7351115a28f279e6f0610d362d40c1f0c6) |
| EvidenceRegistry | [0x87D7…7107](https://explorer-studio.genlayer.com/address/0x87D7bD3d6038FFB69fD39b20950E392650C37107) |
| StewardCourt | [0xb29A…2fB6](https://explorer-studio.genlayer.com/address/0xb29AD5AcAF20B2187e2B4E50A71450b6F95f2fB6) |
| StewardBondVault | [0x26b7…5675](https://explorer-studio.genlayer.com/address/0x26b7714E00279cA83Dc78466bE25798e54d05675) |
| StewardGuard | [0xeA83…83AD](https://explorer-studio.genlayer.com/address/0xeA838677a8C0c3A955722846be490FDc90583AD) |
| StewardVault | [0xFF6F…fd00](https://explorer-studio.genlayer.com/address/0xFF6FcE9432bC416130de3C26b5b0f507880aFd00) |

Network: **Studionet**, chain ID `61999`, RPC `https://studio.genlayer.com/api`, explorer `https://explorer-studio.genlayer.com`, repository-local CLI `genlayer@0.39.1`.

## Source integrity

The readable contract files are the exact files used for tests, mutation checks, lint, and deployment. There are no generated or minified deployment copies. The current deployment source commit is `57fc43cd1c0438e4aaf071822b546509473d8c26`.

```text
contracts/steward_charter.py     d4d13884ff29ad695ebe655ad66c033d3c3006c7308ab76d0f23eb2b1a4820c1
contracts/evidence_registry.py   f7bf6547440f954c18acb191fd211307d6cdecf953d3faceaa7946d8f5d831dd
contracts/steward_court.py       c98b659f2a6dca82fd8af38596df078ff259ab9a06e6e8bf5f6ee0518776be31
contracts/steward_guard.py       70a585ca15e64d38aaeb0b820f7c60a205bc4bdb832ab49b7fee5482e7de0378
contracts/steward_vault.py       e4c4a442435ce81a03afecb9c9c3546c50e5ff1f80599dbebcf23d75b4b67c03
contracts/steward_bond_vault.py  bc4cd665fa91c68647c5cac359fa22f93d787a960b739f3c1da75fe16c342df6
```

## Observed live proof

The current packet records the fresh six-contract deployment, threshold binding, source hashes, and the current source-generation readbacks. The registration-reconciliation behavior is covered by adversarial tests: an unacknowledged registration can be retried before its deadline, and a refunded registration cannot later produce Guard or Vault consequences. The network does not provide a safe control for deliberately dropping one internal child, so that lost-acknowledgment branch is not represented as a forced live observation.

The current source/deployment record is linked from [`final-source-stack-2026-10-10.json`](deploy/proofs/final-source-stack-2026-10-10.json). Historical packets remain in `deploy/proofs/` with explicit superseded status and are not presented as current deployment evidence.

## Frontend

The application is available at [stewardrail.vercel.app](https://stewardrail.vercel.app). It uses an injected EIP-1193 wallet, hard-blocks writes away from Studionet 61999, provides explicit connect/disconnect behavior, converts native amounts exactly to GEN, and tracks parent/child transaction finality. Deployment values come from public environment variables rather than frontend source constants.

Routes include `/workspace`, `/charters/new`, `/charters/[address]`, `/spends/new`, `/spends/[id]`, `/evidence`, `/court`, `/vault`, `/verify`, and `/docs`.

## Local development and verification

```text
npm ci
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

Use the repository-local CLI (`npm exec -- genlayer ...`). Put local public frontend configuration in the ignored `frontend/.env.local`; CI and Vercel use their own public configuration. Never place signer secrets in frontend variables.

## Repository map

```text
contracts/   exact deployable Intelligent Contract sources
reference/   deterministic policy and public semantic fixtures
frontend/    Next.js application
tests/       deterministic, adversarial and Direct Mode coverage
scripts/     manifest, preflight, mutation and validation tooling
deploy/      deployment records and machine-readable proof packets
docs/        architecture, threat model, deployment and live-evidence notes
```

## Limitations

Validator consensus and external web availability affect semantic cases. An authorized issuer proves which bytes were attested, not that the issuer is truthful. Transfer confirmation depends on the network's finalized child transaction and value-credit readback. Studionet is a test network. The canonical packet records observed outcomes only; unobserved scenarios are not implied by the deployment record.

## License

MIT. See [`LICENSE`](LICENSE).
