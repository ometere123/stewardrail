# StewardRail design claims

These are the concrete protocol and engineering claims the repository is built to make defensible.

## GenLayer fit

The primary use case is a jointly governed treasury whose principals deliberately do not trust one another, the agent, or vendors to be the sole judge. Deterministic limits run without consensus. Only semantic mandate compliance uses neutral validators, and their decision controls whether shared GEN can leave custody. Replacing neutral consensus with human approval reintroduces a privileged arbiter and changes the product's trust model.

## Contract quality

Five contracts have narrow responsibilities. Historical mandate versions are immutable. Evidence authenticity is wallet-attested before semantic reasoning. The guard has no custody. The vault has no semantic logic. Court explicitly models reversible economic outcomes. Fail-closed boundaries and exact recipient/amount settlement are visible in source and tests.

## Engineering

The exact readable source is the deployable source. CI checks a SHA manifest, syntax, source invariants, model tests, mutation guards, network lock, and frontend type/build tests. The live proof plan demands both appeal reversal directions and verifies FINALIZED + consensus + execution rather than treating acceptance as success.
