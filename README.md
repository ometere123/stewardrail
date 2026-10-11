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

The deployed BondVault also supports a separate bonded challenge path. A challenge quotes its bond from the spend's frozen policy, is registered through Court, and reaches Guard before any custody consequence. The current fresh-stack packet records an upheld challenge, Guard revocation, BondVault settlement, challenger refund, and repeated idempotent reconciliation.

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

Vault records the recipient and amount from the frozen Guard spend record. `pay(spend_id)` requires a terminal economic `ALLOW`, sufficient treasury, and no prior payment; callers cannot substitute a recipient or amount. The fresh stack paid 1 GEN to the configured recipient and rejected a duplicate payment without creating a child transfer. Threshold recovery remains governed by the Charter rather than an individual owner.

## Canonical Studionet deployment

The fresh corrected source stack is recorded in [`deploy/deployments.json`](deploy/deployments.json) and [`deploy/proofs/canonical-2026-10-11-appeal-safety.json`](deploy/proofs/canonical-2026-10-11-appeal-safety.json). Earlier lifecycle packets are historical records for superseded source generations.

| Contract | Studionet address |
| --- | --- |
| StewardCharter | [0x1538…22F2](https://explorer-studio.genlayer.com/address/0x15389f6824CAD32cAAa16B4fb1f2b825B52122F2) |
| EvidenceRegistry | [0xA6b3…b3BE3](https://explorer-studio.genlayer.com/address/0xA6b358C025C49Af95D516f3AC46305be728b3BE3) |
| StewardCourt | [0x6B65…ffF4](https://explorer-studio.genlayer.com/address/0x6B65f13f64fAdE3825d6517691a6cE20d709ffF4) |
| StewardGuard | [0x7a96…CED7](https://explorer-studio.genlayer.com/address/0x7a96536464BA39D445C56594bE02F0897eaFCED7) |
| StewardVault | [0x3F13…fFe2](https://explorer-studio.genlayer.com/address/0x3F13f96B251485ba65601Df0B97A05a223bafFe2) |
| StewardBondVault | [0x737E…5AfE](https://explorer-studio.genlayer.com/address/0x737EFC982EAf837EeEeFF5a13bC18e8Eb4db5AfE) |

Network: **Studionet**, chain ID `61999`, RPC `https://studio.genlayer.com/api`, explorer `https://explorer-studio.genlayer.com`, repository-local CLI `genlayer@0.39.1`.

## Source integrity

The readable contract files are the exact files used for tests, mutation checks, lint, and deployment. There are no generated or minified deployment copies. The fresh deployment source commit is `8904b225ef65aa46a0212fcb2469bc892ae1b061`; later documentation/proof commits do not change contract bytes.

```text
contracts/steward_charter.py     5f406115787047b62fe2a4f98fa9d5114c4305616a5c918a52477089712105ab
contracts/evidence_registry.py   f7bf6547440f954c18acb191fd211307d6cdecf953d3faceaa7946d8f5d831dd
contracts/steward_court.py       71e7495f624f3c3db86644d80557bbcb2ff9b7b97eaac6c1cc166673f4054e9c
contracts/steward_guard.py       0279c30f0b42da7c0528d67349c8ec2de93ee8692304fbaebc6ba3d5052ff1aa
contracts/steward_vault.py       5fd342442aa7b745b60f9d5197bad6447e357223a3397ba15d6eef6d37de431a
contracts/steward_bond_vault.py  add2daa5d4012819831d8a60450715dbf17fa7d662df63bb073541525471c039
```

## Observed live proof

The canonical packet records the fresh six-contract deployment, threshold-approved mandate v2, source hashes, a semantic ALLOW through Court→Guard→Vault, a substantive ALLOW→REFUSE application reversal, a substantive REFUSE→ALLOW application reversal, a technical-unresolved case that exhausted bounded retries and closed without authority, an upheld bonded challenge with settlement and repeated reconciliation, and a funded 1 GEN payout with an independently credited payment child.

The current source/deployment record is linked from [`canonical-2026-10-11-appeal-safety.json`](deploy/proofs/canonical-2026-10-11-appeal-safety.json). Historical packets remain in `deploy/proofs/` with explicit superseded status and are not presented as current deployment evidence.

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
