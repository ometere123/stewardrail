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

The deployed BondVault also supports a separate bonded challenge path. A challenge quotes its bond from the spend's frozen policy, is registered through Court, and reaches Guard before any custody consequence. In the observed post-payment case, the original recipient payment remained paid, the challenge was upheld, Guard marked the authorization revoked, and 0.1 GEN was reimbursed to Vault from standing collateral before the bond was refunded. A repeated reconciliation delivered the same terminal result without double settlement.

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

Vault records the recipient and amount from the frozen Guard spend record. `pay(spend_id)` requires a terminal economic `ALLOW`, sufficient treasury, and no prior payment; callers cannot substitute a recipient or amount. The observed payment transferred 0.1 GEN to the recorded recipient, and a duplicate payment finalized with execution error. Threshold recovery remains governed by the Charter rather than an individual owner.

## Canonical Studionet deployment

The current source-matched stack is recorded in [`deploy/deployments.json`](deploy/deployments.json) and the machine-readable lifecycle packet is [`deploy/proofs/final-stack-2026-10-10.json`](deploy/proofs/final-stack-2026-10-10.json).

| Contract | Studionet address |
| --- | --- |
| StewardCharter | [0xd985…910d](https://explorer-studio.genlayer.com/address/0xd985d10D59DB717DCD0f335dD1Af6A32122d910d) |
| EvidenceRegistry | [0x6841…8bb9](https://explorer-studio.genlayer.com/address/0x68419Fb7E8db6371f166990765c50e36F1098bb9) |
| StewardCourt | [0xF4B7…22B6](https://explorer-studio.genlayer.com/address/0xF4B7881d93Bd5BA03D15F2e4FA68502A08b122B6) |
| StewardBondVault | [0x3b88…44b6](https://explorer-studio.genlayer.com/address/0x3b8869AcbD3F4c628c6DB10ed355cF097dbC44b6) |
| StewardGuard | [0x8F4b…2C4C](https://explorer-studio.genlayer.com/address/0x8F4b344b3E100FA2F460985b7F802F35E5422C4C) |
| StewardVault | [0x2198…4B7f](https://explorer-studio.genlayer.com/address/0x2198E29C208f000dAEB4150D9C3F3044Add64B7f) |

Network: **Studionet**, chain ID `61999`, RPC `https://studio.genlayer.com/api`, explorer `https://explorer-studio.genlayer.com`, repository-local CLI `genlayer@0.39.1`.

## Source integrity

The readable contract files are the exact files used for tests, mutation checks, lint, and deployment. There are no generated or minified deployment copies. The canonical deployment source commit is `66151accaca6c375f7f978f54c01f01ddaebc7cf`.

```text
contracts/steward_charter.py     726f5a19f5cd66987ed3d568be1c8b6e593801f8e9252b1e78a5f49fa2a37f2d
contracts/evidence_registry.py   f7bf6547440f954c18acb191fd211307d6cdecf953d3faceaa7946d8f5d831dd
contracts/steward_court.py       33a10ee3435f21915e2c6f51096b04f4e2453d527cb2db315cf6b5fa99dc7454
contracts/steward_guard.py       18294b400a0b8a4294a3d0d85737fc0038e239f2439ed723df4993d02af7d60f
contracts/steward_vault.py       2e3f65a9d6ad543aa3ba518376e74c505a90f77ffb8f1bb7638296b6d1d2b088
contracts/steward_bond_vault.py  d5a9f7b3e8731c2716ce58896247b15906dbc76a52471a0898bf3b2303ff269d
```

## Observed live proof

The canonical packet contains finalized deployment and binding receipts, two-principal mandate activation, issuer attestations, a semantic `ALLOW`, Court → Guard → Vault finality, standing deposit, Vault funding, exact 0.1 GEN payment, recipient delivery confirmation, duplicate-payment rejection, an upheld post-payment challenge with 0.1 GEN restitution, bond refund, and idempotent reconciliation. A semantic `REFUSE` is not claimed in this packet; earlier disagreement attempts remain historical records.

Relevant evidence is linked from the packet, including:

- semantic request and Court child: [`0x4a42…`](https://explorer-studio.genlayer.com/tx/0x4a42cea6b618b23712e9536ed71a8002f1a123056d816883acd944b8d2b17ad6);
- terminal Court → Guard → Vault chain: [`0xbb12…`](https://explorer-studio.genlayer.com/tx/0xbb12dd78424de95a54cde78f16702e0d34b055b813fa19023fb37f60d35705e1), [`0xacfa…`](https://explorer-studio.genlayer.com/tx/0xacfa4e00ad8d672b7f072d6b00240d42b41133a938913f6a106ca8f1b6b42826), [`0xe5be…`](https://explorer-studio.genlayer.com/tx/0xe5be4f0d16edf35cfb07819e95e64b2763249eb7bb213635b20cb780ebe95d7a);
- payment and delivery child: [`0x6801…`](https://explorer-studio.genlayer.com/tx/0x680178138525b2ea6835a7661ccd039416e1268afe62752c2d6118388646c152), [`0x1e15…`](https://explorer-studio.genlayer.com/tx/0x1e15bbc3a11cd43acbd90c790dffa475f5adb66a4b6537711d894d80aafb66d8);
- challenge resolution and settlement: [`0x4b1b…`](https://explorer-studio.genlayer.com/tx/0x4b1be2379fda7ed999c39fe356a517cf1b2a9afd9f4fbd2c55453339bcfa686c), [`0xb7da…`](https://explorer-studio.genlayer.com/tx/0xb7daef90b31c3dec85e9cc713ea17c3381045823bf3f6f25663fee5b11e506c8);
- reconciliation retry: [`0x0bf7…`](https://explorer-studio.genlayer.com/tx/0x0bf76f080d592ada2d84b0392ad348cd7de2ff09c5d23b950ab2fdff4881d774).

Historical packets remain in `deploy/proofs/` with explicit superseded status and are not presented as current deployment evidence.

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
