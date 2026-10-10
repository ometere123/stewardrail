# Deployment

StewardRail is locked to stable Studionet 61999.

Use the repository-local CLI only:

```bash
npm ci
npm exec -- genlayer --version
npm exec -- genlayer network set studionet
npm exec -- genlayer network info
node deploy/network-check.mjs
python3 scripts/preflight.py
```

Then deploy in this order: Charter, EvidenceRegistry, Court, BondVault, Guard,
Vault. Verify every receipt is `FINALIZED` with successful execution before
continuing. The repository leaves signer/account selection to the operator's
configured GenLayer CLI rather than embedding a private key.

After deployment, record addresses, hashes and source digests in
`deploy/deployments.json`, set the matching local or Vercel public environment
variables, run the live lifecycle, and only then deploy the frontend.
