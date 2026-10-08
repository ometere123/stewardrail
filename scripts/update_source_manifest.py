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

def build():
    return {
        "schema": 1,
        "policy": "These exact readable files are the deployment inputs; no generated/minified deployable form exists.",
        "contracts": {
            name: {
                "sha256": hashlib.sha256((CONTRACTS / name).read_bytes()).hexdigest(),
                "bytes": (CONTRACTS / name).stat().st_size,
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
