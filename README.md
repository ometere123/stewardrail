# StewardRail

StewardRail is a shared-treasury control system for autonomous agents. Multiple principals approve an immutable mandate, external issuers attest evidence, GenLayer validators answer bounded semantic questions, and deterministic policy decides whether a finalized result may authorize custody.

## What it does

Some treasury rules are mechanical: an amount cap, a rolling exposure limit, or a recipient allow-list. Other questions require interpretation: does an independently retrieved artifact describe the deliverable required by the mandate? StewardRail keeps those concerns separate. Deterministic checks run first; only the bounded semantic question crosses the GenLayer boundary.

The result is not controlled by one owner. A mandate is activated by a principal threshold, evidence is tied to an authorized issuer and exact digest, and no principal has a per-spend semantic override.

## Trust model

- **Principals** approve identical canonical mandate JSON. Historical versions are immutable and each spend records the version used at request time.
- **Agent** submits requests but cannot amend a mandate, adjudicate a semantic case, or withdraw treasury value.
- **Evidence issuers** attest a role, URI and SHA-256 digest for a charter. The registry records issuer authorization and historical validity.
- **StewardCharter** stores principals, thresholds, immutable mandate versions and threshold recovery approvals.
- **EvidenceRegistry** authenticates issuer attestations and their historical status.
- **StewardGuard** performs deterministic screening, bounded semantic adjudication, evidence completeness checks, exposure accounting and terminal economic authorization.
- **StewardCourt** records the primary semantic result and one application appeal without custody authority.
- **StewardVault** holds treasury value and accepts terminal economic decisions only from the configured Guard.
- **StewardBondVault** holds agent standing and challenge bonds; it settles finalized challenge outcomes but does not adjudicate semantics.

Court cannot pay the treasury directly. The custody path is always:

```text
Court (finalized semantic result)
        ↓
Guard (final deterministic economic authorization)
        ↓
Vault (custody and exact payout)
```

## Decision lifecycle

Deterministic refusals are resolved without a jury. A semantic request follows:

```text
request → HELD → evidence attachment/sealing → validator adjudication
        → Court result → application appeal window
        → Guard terminal economic result → Vault authorization → payment
```

The protocol exposes separate fields for primary semantic result, Court effective semantic result, Guard terminal economic result and reason, and Vault terminal/payment state.

An unresolved semantic spend reserves exposure while it remains appealable. Terminal ALLOW remains counted; terminal REFUSE releases the reservation. Optional recipient-scoped rolling policy derives its key from the canonical recipient address, never from an agent-supplied grouping value.

Mandate semantic rules can record an observe-only breach, refuse the current spend, freeze new agent requests, or revoke eligible unpaid authorizations. Freeze clearing and treasury recovery require threshold-approved actions. Already-paid history is not rewritten.

## Evidence provenance

An evidence identity is bound to:

```text
charter | issuer wallet | role | URI | SHA-256 digest
```

The mandate also fixes the HTTPS origin and usage policy. Validators treat fetched pages, manifests and comments as untrusted data; source text cannot change protocol instructions or the output schema. Evidence must have been attested and historically valid no later than the spend request time. An appeal statement is an argument, not a substitute for a missing authenticated role.

`single_use` evidence is consumed only when Guard records a terminal economic ALLOW. Reusable evidence may be used again where the frozen mandate permits it. Terminal REFUSE does not consume a single-use artifact.

## Finalized messages and reconciliation

Irreversible authority messages use finalized internal transactions. A Court terminal record emits to Guard; a finalized Guard authorization then emits to Vault. Guard and Vault terminal records are idempotent and carry a full payload fingerprint, so a reconciliation call can re-deliver an identical missing child without changing the decision or consuming evidence twice.

## Canonical Studionet deployment

The current six-contract stack is recorded in [`deploy/deployments.json`](deploy/deployments.json) and the machine-readable lifecycle packet is [`deploy/proofs/final-fresh-studionet-2026-10-10.json`](deploy/proofs/final-fresh-studionet-2026-10-10.json). Deployment and binding transactions in that record were observed as `FINALIZED` with successful leader execution.

| Contract | Studionet address |
| --- | --- |
| StewardCharter | [0x66D2…0695](https://explorer-studio.genlayer.com/address/0x66D2b55b53A7464d09E2B9666d257B56CB830695) |
| EvidenceRegistry | [0x8551…988F](https://explorer-studio.genlayer.com/address/0x8551DdEE20bD83372A69a7781E64c905d31c988F) |
| StewardCourt | [0x16FA…C50c](https://explorer-studio.genlayer.com/address/0x16FA4B83541194F989c255925eBEa74243DbC50c) |
| StewardBondVault | [0xB944…9Ec3C](https://explorer-studio.genlayer.com/address/0xB944998aBf5D5ee533cE5318DAA7AC0e75D9Ec3C) |
| StewardGuard | [0x5636…75B9](https://explorer-studio.genlayer.com/address/0x563647674D14E7e040210B22e7549e2647AB75B9) |
| StewardVault | [0x49aC…6E15](https://explorer-studio.genlayer.com/address/0x49aC65C93C0BDaBaF5aF8e0DD1a6b98ea34E6E15) |

Network: **Studionet**, chain ID `61999`, RPC `https://studio.genlayer.com/api`, explorer `https://explorer-studio.genlayer.com`, repository-local CLI `genlayer@0.39.1`.

## Observed live evidence

The current packet is deliberately explicit about what was and was not observed on this source stack:

| Scenario | Observation |
| --- | --- |
| Two-principal mandate and threshold BondVault binding | Finalized approvals and binding read back on the canonical stack. |
| Distinct issuer attestations | Vendor and delivery roles were attested by separate configured accounts for the same URI and digest. |
| Semantic REFUSE | Court recorded REFUSE, Guard recorded terminal economic REFUSE, and Vault recorded REFUSE without payment through finalized children. |
| Deterministic ALLOW | Guard and Court ALLOW reached Guard lock/confirmation and Vault terminal recording through finalized children; a subsequent payment was recorded. |
| Duplicate payout | A second `pay` finalized with the expected execution error. |
| Value transfer classification | Studionet reported `value_credited=true`, but the EOA transfer child returned `NO_MAJORITY`; the packet does not call that an independently consensus-confirmed delivery. |
| Semantic ALLOW consensus, fresh reversals, replay, rolling reversal, challenge settlement and recovery | Not observed in this packet; no claim is made for them. |

Historical packets under `deploy/proofs/` are retained with `historical-superseded` status and are not the current deployment evidence.

## Source integrity

The five core contracts plus BondVault use one readable source file each. The same files are tested, linted, mutation-tested and supplied to deployment. The exact SHA-256 values in the current manifest are:

```text
contracts/steward_charter.py     726f5a19f5cd66987ed3d568be1c8b6e593801f8e9252b1e78a5f49fa2a37f2d
contracts/evidence_registry.py   f7bf6547440f954c18acb191fd211307d6cdecf953d3faceaa7946d8f5d831dd
contracts/steward_court.py       424ae88d563b587dd6569df2035e533d44c206672b152c2889ac30c38b743e32
contracts/steward_guard.py       216b1452c3ce67e485af4fb574bfac9cdd2e09916e66ab8677048de27dbe652d
contracts/steward_vault.py       2e3f65a9d6ad543aa3ba518376e74c505a90f77ffb8f1bb7638296b6d1d2b088
contracts/steward_bond_vault.py  1cc62373f3be8d918cfa97fff6ebf61df0b02c80440a30ca9189d17d905dc0a4
```

## Frontend

The application is available at [stewardrail.vercel.app](https://stewardrail.vercel.app). It uses an injected EIP-1193 wallet, hard-blocks writes away from Studionet 61999, preserves a deliberate app-level disconnect, shows GEN amounts with exact 18-decimal conversion, and tracks parent/child transaction finality. Deployment addresses and network values are supplied through public environment variables rather than frontend source constants.

Routes include `/workspace`, `/charters/new`, `/charters/[address]`, `/spends/new`, `/spends/[id]`, `/evidence`, `/court`, `/vault`, `/verify` and `/docs`.

## Local verification

```bash
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

Use `npm exec -- genlayer ...` for repository-local CLI commands. The frontend requires the public `NEXT_PUBLIC_*` deployment variables; local development uses an ignored `frontend/.env.local`, while CI and Vercel use their environment configuration.

## Repository map

```text
contracts/   exact deployable Intelligent Contract sources
reference/   deterministic policy and appeal model
frontend/    Next.js App Router application
tests/       deterministic, adversarial and Direct Mode coverage
scripts/     manifest, preflight, mutation and live tooling
deploy/      deployment records and machine-readable proof packets
docs/        architecture, threat model, deployment and live-evidence notes
```

## Limitations

Validator consensus and external web availability affect semantic cases. An authorized issuer proves which bytes were attested, not that the issuer is truthful. A transfer child can report value credit while lacking an independent consensus-success classification on Studionet; the packet records that distinction. Studionet is a test network and live observations are limited to the scenarios explicitly listed in the current packet.

## License

MIT. See [`LICENSE`](LICENSE).
