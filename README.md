# StewardRail

StewardRail is a shared-treasury control system for autonomous agents. Multiple principals approve an immutable mandate, authorized issuers attest external evidence, GenLayer validators resolve bounded semantic questions, and deterministic policy controls whether a finalized result may authorize custody.

## What StewardRail is

Shared treasuries often combine mechanical rules with questions that require interpretation. A per-spend cap and a rolling exposure limit are deterministic. Whether an authenticated deliverable satisfies a jointly approved brief is a semantic judgment. StewardRail keeps those decisions separate: deterministic screening happens first, and only the bounded semantic residue is sent to GenLayer.

No single principal can unilaterally change a semantic result or withdraw the treasury. A mandate is activated by threshold approval, evidence is bound to an issuer and digest, and custody follows a finalized Court → Guard → Vault chain.

## Trust model

- **Principals** approve identical canonical mandate JSON. Activated mandate versions are immutable and each spend records the version used at request time.
- **Agent** submits requests and evidence but cannot amend a mandate, adjudicate a semantic case, or withdraw treasury value.
- **Evidence issuers** attest a role, URI and SHA-256 digest. The registry records the issuer identity and historical validity.
- **StewardCharter** stores principals, threshold, immutable mandate versions and threshold recovery/unfreeze approvals.
- **EvidenceRegistry** authenticates issuer attestations and supports historical status checks.
- **StewardGuard** performs deterministic screening, evidence checks, semantic adjudication, exposure accounting and terminal economic authorization.
- **StewardCourt** records primary results and application appeals. It never pays the treasury directly.
- **StewardVault** holds treasury value and accepts terminal economic decisions only from the configured Guard.
- **StewardBondVault** holds agent standing and challenge bonds and settles finalized challenge outcomes without adjudicating semantics.

The custody authority path is:

```text
Court finalized semantic result
        ↓
Guard finalized economic authorization
        ↓
Vault custody and exact payout
```

## Decision lifecycle

Deterministic refusals do not require semantic consensus. A semantic request follows:

```text
request → HELD → evidence attachment/sealing → validator adjudication
        → Court primary result → application appeal window
        → Guard terminal economic result → Vault authorization → payment
```

The protocol exposes distinct fields for the primary semantic result, Court effective result, Guard terminal economic result and reason, and Vault payment state. A semantic result that reaches `FINALIZED` with `MAJORITY_DISAGREE` is not accepted; it remains unresolved.

Unresolved semantic spends reserve rolling exposure while an appeal remains possible. Terminal `ALLOW` remains counted and terminal `REFUSE` releases the reservation. Observe-only, refuse, freeze, revoke and clawback consequences are frozen into the approved mandate version.

## Evidence provenance

An evidence identity is bound to:

```text
charter | issuer wallet | role | URI | SHA-256 digest
```

The mandate fixes the allowed HTTPS origin and whether a role is `single_use` or `reusable`. Evidence must have been attested and historically valid no later than the spend request time. Validators treat fetched pages, manifests and comments as untrusted data; source text cannot change protocol instructions or the output schema. An appeal statement is an argument, not a replacement for an authenticated role.

`single_use` evidence is consumed only when Guard records a terminal economic `ALLOW`. Reusable evidence can be used again where the frozen mandate permits it. A terminal `REFUSE` does not consume a single-use artifact.

## Finalized internal messages and reconciliation

Irreversible authority messages use `on="finalized"`. Court emits only to Guard. After Guard applies the deterministic terminal checks, Guard emits the exact economic decision to Vault. Terminal records use full payload fingerprints and are idempotent, so reconciliation can re-deliver an identical missing child without changing the decision or consuming evidence twice.

## Canonical Studionet deployment

The current six-contract stack is recorded in [`deploy/deployments.json`](deploy/deployments.json). Deployment and binding observations are recorded in [`deploy/proofs/fresh-final-source-stack-2026-10-10.json`](deploy/proofs/fresh-final-source-stack-2026-10-10.json).

| Contract | Studionet address |
| --- | --- |
| StewardCharter | [0x3328…1FEA](https://explorer-studio.genlayer.com/address/0x3328380853E2a8e5B59d1aD2563B636d1081FFEA) |
| EvidenceRegistry | [0x36D7…D8119](https://explorer-studio.genlayer.com/address/0x36D72f04c46e30F125F9fdf859E2DB1B227D8119) |
| StewardCourt | [0xCD60…07f8](https://explorer-studio.genlayer.com/address/0xCD60E455a52b12b9e6e93e3171f99843e2f207f8) |
| StewardBondVault | [0x5A62…FB8D](https://explorer-studio.genlayer.com/address/0x5A62cDaebA51A9e7e4FEE90BB4120A2451beFB8D) |
| StewardGuard | [0x9053…7809](https://explorer-studio.genlayer.com/address/0x90539546a6F954E2D5B91c7FE2a5eF21BAAf7809) |
| StewardVault | [0x9C4f…6cEe](https://explorer-studio.genlayer.com/address/0x9C4f1105644e345D12a8921a2D8c04e044b86cEe) |

Network: **Studionet**, chain ID `61999`, RPC `https://studio.genlayer.com/api`, explorer `https://explorer-studio.genlayer.com`, repository-local CLI `genlayer@0.39.1`.

## Observed live evidence

The current packet records only observations from the corrected source stack:

| Scenario | Observation |
| --- | --- |
| Threshold mandate activation | Two distinct principal approvals activated mandate version 1. |
| BondVault binding | Two principal approvals were followed by finalized binding to the deployed Guard and Vault. |
| Authenticated evidence | Separate vendor and delivery issuers attested the exact URI and digest for each semantic case. |
| Semantic REFUSE | A corrected-source semantic case is being re-run against the current stack; see the current proof packet before treating it as canonical evidence. |
| Semantic ALLOW | A corrected-source semantic case is being re-run against the current stack; see the current proof packet before treating it as canonical evidence. |
| Ambiguous/undetermined behavior | Historical attempts with validator disagreement remain labeled historical and were not treated as acceptance. |

The packet records leader execution and protocol consensus separately. Validator entries canceled after quorum are not silently relabeled as successful execution.

## Source integrity

The six readable contract files are the exact files used for tests, lint, mutation checks and deployment. No generated or minified deployment copy exists.

```text
contracts/steward_charter.py     726f5a19f5cd66987ed3d568be1c8b6e593801f8e9252b1e78a5f49fa2a37f2d
contracts/evidence_registry.py   f7bf6547440f954c18acb191fd211307d6cdecf953d3faceaa7946d8f5d831dd
contracts/steward_court.py       7a910177bd663ebafdcb6ea6468715fe7bf591f8da791e5f4a04af3cea943cd1
contracts/steward_guard.py       18294b400a0b8a4294a3d0d85737fc0038e239f2439ed723df4993d02af7d60f
contracts/steward_vault.py       2e3f65a9d6ad543aa3ba518376e74c505a90f77ffb8f1bb7638296b6d1d2b088
contracts/steward_bond_vault.py  1cc62373f3be8d918cfa97fff6ebf61df0b02c80440a30ca9189d17d905dc0a4
```

## Frontend

The application is available at [stewardrail.vercel.app](https://stewardrail.vercel.app). It uses an injected EIP-1193 wallet, hard-blocks writes away from Studionet 61999, preserves deliberate disconnect, converts native amounts exactly to GEN, and tracks parent/child transaction finality. Deployment addresses and network values come from public environment variables rather than frontend source constants.

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

Use `npm exec -- genlayer ...` for repository-local CLI commands. Local frontend configuration belongs in the ignored `frontend/.env.local`; CI and Vercel use their own public environment configuration.

## Repository map

```text
contracts/   exact deployable Intelligent Contract sources
reference/   deterministic policy and public semantic fixtures
frontend/    Next.js App Router application
tests/       deterministic, adversarial and Direct Mode coverage
scripts/     manifest, preflight, mutation and validation tooling
deploy/      deployment records and machine-readable proof packets
docs/        architecture, threat model, deployment and live-evidence notes
```

## Limitations

Validator consensus and external web availability affect semantic cases. An authorized issuer proves which bytes were attested, not that the issuer is truthful. Studionet is a test network. The fresh packet proves accepted semantic primary outcomes and Court delivery; it does not claim that every broader economic lifecycle or every value-transfer child has been independently observed on this source stack.

## License

MIT. See [`LICENSE`](LICENSE).
