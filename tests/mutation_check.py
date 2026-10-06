#!/usr/bin/env python3
"""Small deterministic mutation battery for reviewer-visible safety invariants."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reference.model import classify, HistoricalSpend, ALLOW, REFUSE, HELD, issuer_authorized, appeal_effective, vault_can_pay

m = json.loads((ROOT / "tests" / "fixtures" / "mandate.json").read_text())
r = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
checks = []
checks += [classify(m, 6*10**18, r, "creative", 1000, [])["state"] == REFUSE]
checks += [classify(m, 5*10**17, r, "creative", 1000, [])["state"] == ALLOW]
checks += [classify(m, 2*10**18, r, "creative", 1000, [])["state"] == HELD]
checks += [classify(m, 2*10**18, r, "research", 1000, [])["rules"] == ["brief-fit", "independent-proof"]]
checks += [classify(m, 1, r, "other", 1000, [])["state"] == REFUSE]
checks += [classify(m, 1, "0x9999999999999999999999999999999999999999", "creative", 1000, [])["state"] == REFUSE]
checks += [classify(m, 5*10**18, r, "creative", 1000, [HistoricalSpend(8*10**18, 999, ALLOW)])["state"] == REFUSE]
checks += [issuer_authorized(m, "0x1111111111111111111111111111111111111111", "vendor", "https://vendor.example/a")]
checks += [not issuer_authorized(m, "0x1111111111111111111111111111111111111111", "auditor", "https://vendor.example/a")]
checks += [not issuer_authorized(m, "0x1111111111111111111111111111111111111111", "vendor", "https://vendor.example.evil.test/a")]
checks += [appeal_effective(ALLOW, REFUSE) == REFUSE, appeal_effective(REFUSE, ALLOW) == ALLOW]
checks += [vault_can_pay({"decision": ALLOW, "amount": 1}, False)]
checks += [not vault_can_pay({"decision": REFUSE, "amount": 1}, False)]
checks += [not vault_can_pay({"decision": ALLOW, "amount": 1}, True)]
if not all(checks):
    raise SystemExit("mutation battery failed")
print(f"mutation battery: {len(checks)}/{len(checks)} killed")
