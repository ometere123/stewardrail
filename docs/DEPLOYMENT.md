# Deployment

StewardRail is locked to stable Studionet 61999.

Use the repository-local CLI only:

```bash
npm install
npx genlayer@0.39.1 network set studionet
npx genlayer@0.39.1 network info
node deploy/network-check.mjs
python3 scripts/preflight.py
```

Then deploy in the order documented in `docs/ARCHITECTURE.md`. The helper in `deploy/deploy.mjs` is intentionally conservative: it verifies the network first and leaves signer/account selection to the operator's configured GenLayer CLI rather than embedding a private key.

After deployment, replace the empty values in `deploy/deployments.json`, copy them to `frontend/lib/deployments.ts`, run the live lifecycle, and only then deploy the frontend.
