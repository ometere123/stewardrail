#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
OUT = CONTRACTS / "SOURCE_MANIFEST.json"
FILES = [
    "steward_charter.py", "evidence_registry.py", "steward_court.py",
    "steward_guard.py", "steward_vault.py",
    "steward_bond_vault.py",
]
DEPLOYMENT_LINE_ENDINGS = {name: "lf" for name in FILES}
DEPLOYMENT_LINE_ENDINGS["steward_bond_vault.py"] = "crlf"

def deployment_bytes(name):
    """Return the platform-independent bytes used for deployment verification.

    Five contracts were deployed from LF source and BondVault from CRLF source;
    the explicit per-file policy mirrors the bytes returned by Studio's source
    endpoint and keeps the manifest identical in Linux CI and Windows worktrees.
    """
    data = (CONTRACTS / name).read_bytes().replace(b"\r\n", b"\n")
    if DEPLOYMENT_LINE_ENDINGS[name] == "crlf":
        return data.replace(b"\n", b"\r\n")
    return data

def build():
    return {
        "schema": 1,
        "policy": "These exact readable files are the deployment inputs; the manifest uses the recorded per-file line-ending bytes for cross-platform verification; no generated/minified deployable form exists.",
        "contracts": {
            name: {
                "lineEnding": DEPLOYMENT_LINE_ENDINGS[name],
                "sha256": hashlib.sha256(deployment_bytes(name)).hexdigest(),
                "bytes": len(deployment_bytes(name)),
            }
            for name in FILES
        },
    }

p = argparse.ArgumentParser()
p.add_argument("--check", action="store_true")
a = p.parse_args()
expected = build()
if a.check:
    if not OUT.exists() or json.loads(OUT.read_text()) != expected:
        raise SystemExit("SOURCE_MANIFEST.json is stale; run scripts/update_source_manifest.py")
    print("source manifest: PASS")
else:
    OUT.write_text(json.dumps(expected, indent=2) + "\n")
    print(OUT)
