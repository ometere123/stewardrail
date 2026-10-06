"""Pure deterministic model used by tests and mutation checks.

This does not adjudicate semantics. It models the parts that must remain exactly
reproducible off-chain: mandate validation, deterministic gating, issuer policy,
appeal reversal, and vault terminality.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import urlparse
import json

ALLOW = "allow"
REFUSE = "refuse"
HELD = "held"


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest_json(value) -> str:
    return sha256(canonical_json(value).encode()).hexdigest()


def normalize_address(value: str) -> str:
    value = str(value).lower()
    if not value.startswith("0x") or len(value) != 42:
        raise ValueError("invalid address")
    if any(ch not in "0123456789abcdef" for ch in value[2:]):
        raise ValueError("invalid address")
    return value


def origin(uri: str) -> str:
    p = urlparse(uri)
    if p.scheme.lower() != "https" or not p.hostname or p.username or p.password:
        return ""
    return f"https://{p.hostname.lower()}" + (f":{p.port}" if p.port else "")


def validate_mandate(m: dict) -> None:
    for key in ("name", "deterministic", "semantic_rules", "issuers", "appeal"):
        if key not in m:
            raise ValueError(f"missing {key}")
    d = m["deterministic"]
    if not isinstance(d.get("max_per_spend"), int) or isinstance(d.get("max_per_spend"), bool) or d["max_per_spend"] <= 0:
        raise ValueError("bad max_per_spend")
    rolling = d.get("rolling_limit", {})
    if int(rolling.get("seconds", 0)) <= 0 or int(rolling.get("amount", 0)) <= 0:
        raise ValueError("bad rolling_limit")
    ids = set()
    roles = set()
    for rule in m["semantic_rules"]:
        rid = str(rule.get("id", ""))
        if not rid or rid in ids:
            raise ValueError("bad rule id")
        ids.add(rid)
        if rule.get("when", {}).get("type") not in {"always", "amount_gte", "category_in"}:
            raise ValueError("bad trigger")
        if not rule.get("evidence_roles"):
            raise ValueError("missing evidence role")
        roles |= {str(x) for x in rule["evidence_roles"]}
    issuer_roles = set()
    for item in m["issuers"]:
        normalize_address(item["address"])
        if not item.get("origins"):
            raise ValueError("missing origin")
        if any(origin(str(x)) != str(x).lower().rstrip("/") for x in item["origins"]):
            raise ValueError("bad origin")
        issuer_roles.add(str(item["role"]))
    if not roles <= issuer_roles:
        raise ValueError("uncovered role")
    if int(m["appeal"].get("window_seconds", 0)) <= 0:
        raise ValueError("bad appeal window")


@dataclass(frozen=True)
class HistoricalSpend:
    amount: int
    at: int
    state: str


def classify(mandate: dict, amount: int, recipient: str, category: str, now: int, history: list[HistoricalSpend]) -> dict:
    d = mandate["deterministic"]
    if amount <= 0:
        return {"state": REFUSE, "rules": ["amount_positive"]}
    if amount > d["max_per_spend"]:
        return {"state": REFUSE, "rules": ["max_per_spend"]}
    rolling = d["rolling_limit"]
    floor = now - rolling["seconds"]
    exposure = amount + sum(x.amount for x in history if floor < x.at <= now and x.state != REFUSE)
    if exposure > rolling["amount"]:
        return {"state": REFUSE, "rules": ["rolling_limit"]}
    cats = d.get("category_allowlist", [])
    if cats and category not in cats:
        return {"state": REFUSE, "rules": ["category_allowlist"]}
    denied = {normalize_address(x) for x in d.get("recipient_denylist", [])}
    if normalize_address(recipient) in denied:
        return {"state": REFUSE, "rules": ["recipient_denylist"]}
    fired = []
    for rule in mandate["semantic_rules"]:
        w = rule["when"]
        typ = w["type"]
        yes = typ == "always"
        if typ == "amount_gte":
            yes = amount >= int(w.get("value", 0))
        if typ == "category_in":
            yes = category in w.get("values", [])
        if yes:
            fired.append(rule["id"])
    return {"state": HELD if fired else ALLOW, "rules": fired}


def issuer_authorized(mandate: dict, issuer: str, role: str, uri: str) -> bool:
    who = normalize_address(issuer)
    got_origin = origin(uri)
    for item in mandate["issuers"]:
        if normalize_address(item["address"]) == who and item["role"] == role:
            return got_origin in {str(x).lower().rstrip("/") for x in item["origins"]}
    return False


def evidence_active_at(attested_at: int, revoked_at: int, at: int) -> bool:
    return attested_at > 0 and attested_at <= at and (revoked_at == 0 or revoked_at > at)


def appeal_effective(primary: str, appeal: str | None) -> str:
    if primary not in (ALLOW, REFUSE):
        raise ValueError("bad primary")
    if appeal is None:
        return primary
    if appeal not in (ALLOW, REFUSE):
        raise ValueError("bad appeal")
    return appeal


def vault_can_pay(terminal: dict | None, paid: bool) -> bool:
    return bool(terminal and terminal.get("decision") == ALLOW and not paid and int(terminal.get("amount", 0)) > 0)
