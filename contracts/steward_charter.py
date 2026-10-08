# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import hashlib
import json


def _addr(value) -> str:
    """Normalize SDK Address objects and external hex-address strings."""
    if hasattr(value, "as_hex"):
        return str(value.as_hex).lower()
    address = Address(str(value))
    return str(getattr(address, "as_hex", address)).lower()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_value(raw):
    if isinstance(raw, (dict, list)):
        return raw
    return json.loads(str(raw))


def _canonical(raw) -> str:
    return json.dumps(_json_value(raw), separators=(",", ":"), sort_keys=True)


def _action_hash(kind: str, target: str, to: str, amount: int, nonce: int) -> str:
    return _sha("|".join([str(kind), _addr(target), _addr(to), str(int(amount)), str(int(nonce))]))


class StewardCharter(gl.Contract):
    """Threshold governance and immutable mandate history for a shared treasury."""

    agent: Address
    threshold: u256
    principal_count: u256
    current_version: u256
    principal_at: TreeMap[u256, str]
    principal_flag: TreeMap[str, u256]
    proposal_json: TreeMap[str, str]
    proposal_approvals: TreeMap[str, u256]
    approved_proposal: TreeMap[str, u256]
    version_json: TreeMap[u256, str]
    version_digest: TreeMap[u256, str]
    digest_version: TreeMap[str, u256]
    recovery_approvals: TreeMap[str, u256]
    recovery_approved_by: TreeMap[str, u256]
    recovery_ready: TreeMap[str, u256]

    def __init__(self, principals_json: str, threshold: int, agent: str, initial_mandate_json: str):
        principals = _json_value(principals_json)
        if not isinstance(principals, list) or len(principals) < 2:
            raise gl.vm.UserError("[EXPECTED] at least two principals are required")
        if int(threshold) < 2 or int(threshold) > len(principals):
            raise gl.vm.UserError("[EXPECTED] threshold must be between 2 and principal count")
        seen = []
        for raw in principals:
            address = _addr(str(raw))
            if address in seen:
                raise gl.vm.UserError("[EXPECTED] duplicate principal")
            seen.append(address)
        if _addr(gl.message.sender_address) not in seen:
            raise gl.vm.UserError("[EXPECTED] deployer must be a principal")

        self.agent = Address(str(agent))
        self.threshold = u256(int(threshold))
        self.principal_count = u256(len(seen))
        self.current_version = u256(0)
        for index, address in enumerate(seen):
            self.principal_at[u256(index)] = address
            self.principal_flag[address] = u256(1)

        canonical = self._validate_mandate(initial_mandate_json)
        self.proposal_json[_sha(canonical)] = canonical

    def _require_principal(self) -> str:
        caller = _addr(gl.message.sender_address)
        if int(self.principal_flag.get(caller, u256(0))) != 1:
            raise gl.vm.UserError("[EXPECTED] caller is not a charter principal")
        return caller

    def _validate_mandate(self, raw) -> str:
        try:
            m = _json_value(raw)
        except Exception as exc:
            raise gl.vm.UserError("[EXPECTED] mandate must be valid JSON") from exc
        if not isinstance(m, dict):
            raise gl.vm.UserError("[EXPECTED] mandate must be an object")
        for key in ("name", "deterministic", "semantic_rules", "issuers", "appeal"):
            if key not in m:
                raise gl.vm.UserError("[EXPECTED] mandate missing " + key)

        deterministic = m["deterministic"]
        if not isinstance(deterministic, dict):
            raise gl.vm.UserError("[EXPECTED] deterministic policy must be an object")
        max_per = deterministic.get("max_per_spend")
        if isinstance(max_per, bool) or not isinstance(max_per, int) or max_per <= 0:
            raise gl.vm.UserError("[EXPECTED] max_per_spend must be a positive integer")
        rolling = deterministic.get("rolling_limit")
        if not isinstance(rolling, dict):
            raise gl.vm.UserError("[EXPECTED] rolling_limit must be an object")
        if int(rolling.get("seconds", 0)) <= 0 or int(rolling.get("amount", 0)) <= 0:
            raise gl.vm.UserError("[EXPECTED] rolling_limit needs positive seconds and amount")

        rules = m["semantic_rules"]
        if not isinstance(rules, list) or len(rules) < 1 or len(rules) > 16:
            raise gl.vm.UserError("[EXPECTED] semantic_rules must contain 1..16 rules")
        rule_ids = []
        required_roles = []
        for rule in rules:
            if not isinstance(rule, dict):
                raise gl.vm.UserError("[EXPECTED] semantic rule must be an object")
            rid = str(rule.get("id", "")).strip()
            question = str(rule.get("question", "")).strip()
            if rid == "" or rid in rule_ids or len(rid) > 48 or question == "" or len(question) > 600:
                raise gl.vm.UserError("[EXPECTED] invalid semantic rule id/question")
            rule_ids.append(rid)
            when = rule.get("when", {})
            if not isinstance(when, dict) or str(when.get("type", "")) not in ("always", "amount_gte", "category_in"):
                raise gl.vm.UserError("[EXPECTED] unsupported semantic trigger")
            roles = rule.get("evidence_roles", [])
            if not isinstance(roles, list) or len(roles) < 1 or len(roles) > 8:
                raise gl.vm.UserError("[EXPECTED] each semantic rule needs 1..8 evidence roles")
            for role in roles:
                role_name = str(role).strip()
                if role_name == "" or len(role_name) > 48:
                    raise gl.vm.UserError("[EXPECTED] invalid evidence role")
                if role_name not in required_roles:
                    required_roles.append(role_name)

        issuers = m["issuers"]
        if not isinstance(issuers, list) or len(issuers) < 1 or len(issuers) > 32:
            raise gl.vm.UserError("[EXPECTED] issuers must contain 1..32 entries")
        coverage = []
        for issuer in issuers:
            if not isinstance(issuer, dict):
                raise gl.vm.UserError("[EXPECTED] issuer entry must be an object")
            address = _addr(str(issuer.get("address", "")))
            role = str(issuer.get("role", "")).strip()
            origins = issuer.get("origins", [])
            if role == "" or not isinstance(origins, list) or len(origins) < 1:
                raise gl.vm.UserError("[EXPECTED] issuer needs role and at least one https origin")
            for origin in origins:
                origin_text = str(origin).strip().lower().rstrip("/")
                if not origin_text.startswith("https://") or "/" in origin_text[8:]:
                    raise gl.vm.UserError("[EXPECTED] issuer origins must be scheme+host only")
            marker = role + "|" + address
            if marker in coverage:
                raise gl.vm.UserError("[EXPECTED] duplicate issuer-role pair")
            coverage.append(marker)
        for role in required_roles:
            if not any(item.startswith(role + "|") for item in coverage):
                raise gl.vm.UserError("[EXPECTED] semantic role has no authorized issuer: " + role)

        appeal = m["appeal"]
        if not isinstance(appeal, dict) or int(appeal.get("window_seconds", 0)) <= 0:
            raise gl.vm.UserError("[EXPECTED] appeal.window_seconds must be positive")
        if int(appeal.get("bond", 0)) != 0:
            raise gl.vm.UserError("[EXPECTED] v1 participant-gated appeals do not accept a monetary bond")
        return _canonical(m)

    @gl.public.write
    def approve_mandate(self, mandate_json: str) -> None:
        caller = self._require_principal()
        canonical = self._validate_mandate(mandate_json)
        digest = _sha(canonical)
        if int(self.digest_version.get(digest, u256(0))) > 0:
            raise gl.vm.UserError("[EXPECTED] mandate is already active")
        if self.proposal_json.get(digest, "") == "":
            self.proposal_json[digest] = canonical
        key = digest + "|" + caller
        if int(self.approved_proposal.get(key, u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] principal already approved this proposal")
        self.approved_proposal[key] = u256(1)
        count = int(self.proposal_approvals.get(digest, u256(0))) + 1
        self.proposal_approvals[digest] = u256(count)
        if count >= int(self.threshold):
            version = int(self.current_version) + 1
            self.version_json[u256(version)] = canonical
            self.version_digest[u256(version)] = digest
            self.digest_version[digest] = u256(version)
            self.current_version = u256(version)

    @gl.public.write
    def approve_recovery(self, vault: str, to: str, amount: int, nonce: int) -> None:
        caller = self._require_principal()
        if int(amount) <= 0 or int(nonce) < 0:
            raise gl.vm.UserError("[EXPECTED] recovery amount must be positive and nonce non-negative")
        action = _action_hash("vault-recovery", str(vault), str(to), int(amount), int(nonce))
        key = action + "|" + caller
        if int(self.recovery_approved_by.get(key, u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] principal already approved this recovery")
        self.recovery_approved_by[key] = u256(1)
        count = int(self.recovery_approvals.get(action, u256(0))) + 1
        self.recovery_approvals[action] = u256(count)
        if count >= int(self.threshold):
            self.recovery_ready[action] = u256(1)

    @gl.public.view
    def recovery_is_approved(self, vault: str, to: str, amount: int, nonce: int) -> bool:
        action = _action_hash("vault-recovery", str(vault), str(to), int(amount), int(nonce))
        return int(self.recovery_ready.get(action, u256(0))) == 1

    @gl.public.view
    def current(self) -> str:
        version = int(self.current_version)
        return json.dumps({
            "version": version,
            "digest": "" if version == 0 else self.version_digest[u256(version)],
            "mandate": "" if version == 0 else self.version_json[u256(version)],
            "agent": _addr(self.agent),
            "threshold": int(self.threshold),
            "principals": self._principals(),
        })

    @gl.public.view
    def mandate_at(self, version: int) -> str:
        v = int(version)
        if v <= 0 or v > int(self.current_version):
            raise gl.vm.UserError("[EXPECTED] unknown mandate version")
        return self.version_json[u256(v)]

    @gl.public.view
    def digest_at(self, version: int) -> str:
        v = int(version)
        if v <= 0 or v > int(self.current_version):
            raise gl.vm.UserError("[EXPECTED] unknown mandate version")
        return self.version_digest[u256(v)]

    @gl.public.view
    def is_principal(self, address: str) -> bool:
        return int(self.principal_flag.get(_addr(str(address)), u256(0))) == 1

    @gl.public.view
    def info(self) -> str:
        return json.dumps({
            "agent": _addr(self.agent),
            "threshold": int(self.threshold),
            "principals": self._principals(),
            "current_version": int(self.current_version),
            "release": "steward-charter/1",
        })

    def _principals(self) -> list:
        out = []
        i = 0
        while i < int(self.principal_count):
            out.append(self.principal_at[u256(i)])
            i += 1
        return out
