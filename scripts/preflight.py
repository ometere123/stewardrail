#!/usr/bin/env python3
from pathlib import Path
import ast, json, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
network = json.loads((ROOT / "NETWORK_LOCK.json").read_text())
assert network == {
  "name": "studionet",
  "chain_id": 61999,
  "chain_id_hex": "0xF22F",
  "rpc": "https://studio.genlayer.com/api",
  "explorer": "https://explorer-studio.genlayer.com",
  "cli": "0.39.1",
  "genlayer_js": "1.1.8",
  "policy": "All deployments, writes, proof packets and frontend signing must hard-gate this chain. No alternate network is permitted for this repository."
}
required = [
    "contracts/steward_charter.py", "contracts/evidence_registry.py", "contracts/steward_guard.py",
    "contracts/steward_court.py", "contracts/steward_vault.py", "frontend/package.json",
    "docs/ARCHITECTURE.md", "docs/THREAT_MODEL.md", "docs/LIVE_TEST_PLAN.md",
    "STEWARDRAIL_CODEX_MASTER_HANDOFF.txt",
]
for rel in required:
    if not (ROOT / rel).exists():
        raise SystemExit(f"missing required file: {rel}")
for path in (ROOT / "contracts").glob("*.py"):
    source = path.read_text()
    tree = ast.parse(source)
    if 'py-genlayer:' not in source.splitlines()[0]:
        raise SystemExit(f"runtime pin missing: {path.name}")
    if 'raise Exception(' in source:
        raise SystemExit(f"bare user-facing Exception is forbidden: {path.name}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and ast.unparse(node.exc.func) == "Exception":
            raise SystemExit(f"bare user-facing Exception is forbidden: {path.name}:{node.lineno}")
    for marker in (
        'str(Address(', 'str(gl.message.sender_address)', 'str(gl.message.contract_address)',
        'str(self.agent)', 'str(self.charter)', 'str(self.registry)', 'str(self.court)', 'str(self.guard)',
    ):
        if marker in source:
            raise SystemExit(f"unsafe Address serialization in {path.name}: {marker}")
if (ROOT / "contracts" / "build").exists() or list((ROOT / "contracts").glob("*.min.py")):
    raise SystemExit("generated/minified deployable source is forbidden")
front_roots = [ROOT / "frontend" / "app", ROOT / "frontend" / "components", ROOT / "frontend" / "lib"]
front = "\n".join(p.read_text(errors="ignore") for base in front_roots for p in base.rglob("*") if p.is_file())
for forbidden in ("walletconnect", "@reown", "privy", "supabase", "firebase", "/api/"):
    if forbidden.lower() in front.lower():
        raise SystemExit(f"forbidden frontend/backend dependency marker: {forbidden}")
subprocess.run([sys.executable, str(ROOT / "scripts" / "update_source_manifest.py"), "--check"], check=True)
print("preflight: PASS")
