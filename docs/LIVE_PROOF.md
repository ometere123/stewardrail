# Live proof index

This file is a placeholder until a fresh Studionet 61999 deployment is completed.

Do **not** turn it into a success claim from local tests. Follow `docs/LIVE_TEST_PLAN.md`, put machine-readable transaction evidence under `deploy/proofs/`, and then replace this file with a concise index mapping each submission claim to its FINALIZED successful transaction and post-state read.

The two most important economic proofs are:

1. semantic primary `ALLOW` -> application appeal `REFUSE` -> finalized terminal refusal -> vault payout fails;
2. semantic primary `REFUSE` -> application appeal `ALLOW` -> finalized terminal allow -> vault pays the exact recipient/amount once.
