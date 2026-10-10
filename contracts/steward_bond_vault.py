# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import datetime
import json
from urllib.parse import urlparse


def _addr(value) -> str:
    if hasattr(value, "as_hex"):
        return str(value.as_hex).lower()
    address = Address(str(value))
    return str(getattr(address, "as_hex", address)).lower()


def _origin(uri: str) -> str:
    parsed = urlparse(str(uri))
    if parsed.scheme.lower() != "https" or parsed.hostname is None or parsed.username is not None or parsed.password is not None:
        return ""
    port = "" if parsed.port is None else ":" + str(parsed.port)
    return "https://" + parsed.hostname.lower() + port


@gl.evm.contract_interface
class _Payee:
    class View:
        pass
    class Write:
        pass


class StewardBondVault(gl.Contract):
    """Collateral and challenge settlement; it never adjudicates semantics."""

    charter: Address
    agent: Address
    guard: Address
    court: Address
    vault: Address
    standing: u256
    locked: u256
    challenge_count: u256
    challenge_state: TreeMap[u256, str]
    challenge_spend: TreeMap[u256, u256]
    challenge_bond: TreeMap[u256, u256]
    challenge_challenger: TreeMap[u256, str]
    challenge_cause: TreeMap[u256, str]
    challenge_evidence: TreeMap[u256, str]
    challenge_deadline: TreeMap[u256, u256]
    challenge_registration_deadline: TreeMap[u256, u256]
    challenge_registered: TreeMap[u256, u256]
    challenge_settlement: TreeMap[u256, str]
    challenger_losses: TreeMap[str, u256]
    challenger_loss_at: TreeMap[str, u256]
    challenge_by_spend: TreeMap[u256, u256]
    open_by_spend: TreeMap[u256, u256]
    upheld_by_spend: TreeMap[u256, u256]
    locked_by_spend: TreeMap[u256, u256]
    lock_deadline: TreeMap[u256, u256]
    challenge_attempts_by_spend: TreeMap[u256, u256]
    challenge_window_end_by_spend: TreeMap[u256, u256]
    challenge_max_attempts_by_spend: TreeMap[u256, u256]

    def __init__(self, charter: str, agent: str):
        self.charter = Address(str(charter))
        info = json.loads(str(gl.get_contract_at(self.charter).view().current()))
        self.agent = Address(str(agent))
        if _addr(info["agent"]) != _addr(self.agent):
            raise gl.vm.UserError("[EXPECTED] collateral agent does not match charter")
        self.guard = Address("0x0000000000000000000000000000000000000000")
        self.court = Address("0x0000000000000000000000000000000000000000")
        self.vault = Address("0x0000000000000000000000000000000000000000")
        self.standing = u256(0)
        self.locked = u256(0)
        self.challenge_count = u256(0)

    @gl.public.write
    def bind(self, guard: str, vault: str) -> None:
        if _addr(self.guard) != _addr("0x0000000000000000000000000000000000000000"):
            raise gl.vm.UserError("[EXPECTED] collateral bindings are immutable")
        approved = bool(gl.get_contract_at(self.charter).view().bond_vault_is_approved(_addr(gl.message.contract_address), str(guard), str(vault)))
        if not approved:
            raise gl.vm.UserError("[EXPECTED] collateral binding lacks threshold approval")
        self.guard = Address(str(guard))
        self.vault = Address(str(vault))
        guard_info = json.loads(str(gl.get_contract_at(self.guard).view().info()))
        self.court = Address(str(guard_info["court"]))

    @gl.public.write.payable
    def deposit_standing(self) -> None:
        if gl.message.sender_address != self.agent:
            raise gl.vm.UserError("[EXPECTED] only the configured agent may deposit standing collateral")
        value = int(gl.message.value)
        if value <= 0:
            raise gl.vm.UserError("[EXPECTED] standing deposit must be positive")
        self.standing = u256(int(self.standing) + value)

    @gl.public.write
    def withdraw_standing(self, to: str, amount: int) -> None:
        if gl.message.sender_address != self.agent:
            raise gl.vm.UserError("[EXPECTED] only the configured agent may withdraw standing collateral")
        value = int(amount)
        available = int(self.standing) - int(self.locked)
        if value <= 0 or value > available:
            raise gl.vm.UserError("[EXPECTED] standing collateral is locked or insufficient")
        self.standing = u256(int(self.standing) - value)
        _Payee(Address(str(to))).emit_transfer(value=u256(value))

    @gl.public.write
    def lock_exposure(self, spend_id: int, amount: int, deadline: int) -> None:
        if gl.message.sender_address != self.guard:
            raise gl.vm.UserError("[EXPECTED] only the bound guard may lock standing exposure")
        value = int(amount)
        if value <= 0 or int(deadline) <= 0:
            raise gl.vm.UserError("[EXPECTED] invalid standing exposure lock")
        key = u256(int(spend_id))
        existing_window = int(self.challenge_window_end_by_spend.get(key, u256(0)))
        existing_max = int(self.challenge_max_attempts_by_spend.get(key, u256(0)))
        if existing_window > 0 and existing_window != int(deadline):
            raise gl.vm.UserError("[EXPECTED] conflicting frozen challenge policy")
        self.challenge_window_end_by_spend[key] = u256(int(deadline))
        # The attempt limit is snapshotted at challenge registration, after
        # Guard has supplied the frozen spend context. Keeping lock replay
        # independent of a Guard read makes failed child delivery safe.
        existing = int(self.locked_by_spend.get(key, u256(0)))
        existing_deadline = int(self.lock_deadline.get(key, u256(0)))
        if existing_deadline > 0:
            if existing != value:
                raise gl.vm.UserError("[EXPECTED] conflicting standing exposure lock")
            if existing_deadline != int(deadline):
                raise gl.vm.UserError("[EXPECTED] conflicting standing exposure lock")
            gl.get_contract_at(self.guard).emit(on="finalized").confirm_exposure_lock(
                int(spend_id), existing, int(deadline), _addr(self.vault)
            )
            return
        available = max(0, int(self.standing) - int(self.locked))
        # A challengeable authorization is either fully backed or economically refused.
        # Partial collateral must never create a partially payable obligation.
        secured = value if available >= value else 0
        self.locked_by_spend[key] = u256(secured)
        self.lock_deadline[key] = u256(int(deadline))
        self.locked = u256(int(self.locked) + secured)
        gl.get_contract_at(self.guard).emit(on="finalized").confirm_exposure_lock(
            int(spend_id), secured, int(deadline), _addr(self.vault)
        )

    @gl.public.write
    def release_exposure(self, spend_id: int) -> None:
        if gl.message.sender_address != self.guard:
            raise gl.vm.UserError("[EXPECTED] only the bound guard may release standing exposure")
        key = u256(int(spend_id))
        value = int(self.locked_by_spend.get(key, u256(0)))
        if value <= 0:
            return
        self.locked = u256(int(self.locked) - value)
        self.locked_by_spend[key] = u256(0)

    @gl.public.write
    def release_expired_exposure(self, spend_id: int) -> None:
        """Permissionless release after the frozen challenge window has ended."""
        key = u256(int(spend_id))
        value = int(self.locked_by_spend.get(key, u256(0)))
        if value <= 0:
            return
        deadline = int(self.lock_deadline.get(key, u256(0)))
        if deadline <= 0 or int(datetime.datetime.now().timestamp()) < deadline:
            raise gl.vm.UserError("[EXPECTED] standing exposure challenge window is still open")
        if int(self.open_by_spend.get(key, u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] open challenge still secures this exposure")
        if int(self.upheld_by_spend.get(key, u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] upheld challenge still secures this exposure")
        if self._future_challenge_permitted(spend_id):
            raise gl.vm.UserError("[EXPECTED] future challenge remains permissible for this exposure")
        spend = json.loads(str(gl.get_contract_at(self.guard).view().get_spend(int(spend_id))))
        if str(spend.get("terminal_economic", "")) not in ("allow", "refuse"):
            raise gl.vm.UserError("[EXPECTED] terminal economic outcome is not settled")
        self.locked = u256(int(self.locked) - value)
        self.locked_by_spend[key] = u256(0)

    def _issuer_policy(self, mandate: dict, issuer: str, role: str):
        for entry in mandate.get("issuers", []):
            if _addr(entry.get("address", "")) == _addr(issuer) and str(entry.get("role", "")) == str(role):
                return entry
        return None

    def _validate_challenge_evidence(self, spend: dict, evidence_json: str) -> list:
        try:
            items = evidence_json if isinstance(evidence_json, list) else json.loads(str(evidence_json))
        except Exception as exc:
            raise gl.vm.UserError("[EXPECTED] challenge evidence must be valid JSON") from exc
        if not isinstance(items, list) or len(items) == 0 or len(items) > 8:
            raise gl.vm.UserError("[EXPECTED] challenge evidence must contain 1..8 items")
        guard_info = json.loads(str(gl.get_contract_at(self.guard).view().info()))
        registry = gl.get_contract_at(Address(str(guard_info["registry"]))).view()
        context = json.loads(str(gl.get_contract_at(self.guard).view().appeal_context(int(spend["id"]))))
        mandate = context["mandate"]
        stamp = int(datetime.datetime.now().timestamp())
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                raise gl.vm.UserError("[EXPECTED] challenge evidence item must be an object")
            issuer = _addr(item.get("issuer", ""))
            role = str(item.get("role", ""))
            uri = str(item.get("uri", ""))
            digest = str(item.get("digest", "")).lower()
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise gl.vm.UserError("[EXPECTED] challenge evidence digest must be sha256 hex")
            policy = self._issuer_policy(mandate, issuer, role)
            allowed = [str(x).lower().rstrip("/") for x in policy.get("origins", [])] if policy is not None else []
            if policy is None or _origin(uri) not in allowed:
                raise gl.vm.UserError("[EXPECTED] challenge evidence issuer, role, or origin is not authorized")
            usage = "reusable" if str(policy.get("usage", "single_use")) == "reusable" else "single_use"
            if str(item.get("usage", usage)) != usage:
                raise gl.vm.UserError("[EXPECTED] challenge evidence usage does not match frozen issuer policy")
            if not bool(registry.status_at(_addr(self.charter), issuer, role, uri, digest, stamp)):
                raise gl.vm.UserError("[EXPECTED] challenge evidence is not historically attested")
            normalized.append({"issuer": issuer, "role": role, "uri": uri, "digest": digest, "usage": usage})
        normalized.sort(key=lambda item: "|".join([item["issuer"], item["role"], item["uri"], item["digest"]]))
        return normalized

    @gl.public.view
    def quote_bond(self, challenged_value: int, spend_id: int = -1) -> int:
        value = int(challenged_value)
        if value <= 0:
            raise gl.vm.UserError("[EXPECTED] challenged value must be positive")
        if int(spend_id) >= 0:
            context = json.loads(str(gl.get_contract_at(self.guard).view().appeal_context(int(spend_id))))
            mandate = context["mandate"]
        else:
            current = json.loads(str(gl.get_contract_at(self.charter).view().current()))
            mandate = json.loads(str(current["mandate"]))
        policy = mandate["challenge"]
        floor = int(policy["bond_floor"])
        fraction = (value * int(policy["bond_bps"])) // 10000
        challenger_key = _addr(gl.message.sender_address)
        losses = int(self.challenger_losses.get(challenger_key, u256(0)))
        last = int(self.challenger_loss_at.get(challenger_key, u256(0)))
        if last > 0:
            elapsed = max(0, int(datetime.datetime.now().timestamp()) - last)
            losses = max(0, losses - elapsed // int(policy["decay_seconds"]))
        multiplier = min(int(policy["max_multiplier_bps"]), 10000 + losses * 5000)
        return (max(floor, fraction) * multiplier + 9999) // 10000

    @gl.public.write.payable
    def open_challenge(self, spend_id: int, challenged_value: int, cause: str, evidence_json: str) -> None:
        if _addr(self.guard) == _addr("0x0000000000000000000000000000000000000000"):
            raise gl.vm.UserError("[EXPECTED] collateral bindings are not initialized")
        if gl.message.sender_address == self.agent:
            raise gl.vm.UserError("[EXPECTED] agent cannot challenge its own authorization")
        if len(str(cause).strip()) == 0 or len(str(cause)) > 240:
            raise gl.vm.UserError("[EXPECTED] challenge cause is invalid")
        spend = json.loads(str(gl.get_contract_at(self.guard).view().get_spend(int(spend_id))))
        spend["id"] = int(spend_id)
        if int(spend.get("amount", 0)) != int(challenged_value) or str(spend.get("terminal_economic", "")) != "allow":
            raise gl.vm.UserError("[EXPECTED] spend is not challengeable")
        context = json.loads(str(gl.get_contract_at(self.guard).view().appeal_context(int(spend_id))))
        policy = context["mandate"]["challenge"]
        anchor = int(spend.get("terminal_at", spend.get("requested_at", 0)))
        if int(datetime.datetime.now().timestamp()) > anchor + int(policy["window_seconds"]):
            raise gl.vm.UserError("[EXPECTED] challenge window has expired")
        if int(self.open_by_spend.get(u256(int(spend_id)), u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] an open challenge already exists")
        if int(self.upheld_by_spend.get(u256(int(spend_id)), u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] an upheld challenge already exhausted this spend")
        attempts = int(self.challenge_attempts_by_spend.get(u256(int(spend_id)), u256(0)))
        policy_key = u256(int(spend_id))
        frozen_window_end = int(self.challenge_window_end_by_spend.get(policy_key, u256(0)))
        frozen_max_attempts = int(self.challenge_max_attempts_by_spend.get(policy_key, u256(0)))
        if frozen_window_end <= 0:
            frozen_window_end = anchor + int(policy["window_seconds"])
        if frozen_max_attempts <= 0:
            frozen_max_attempts = int(policy.get("max_challenges", 2))
        if int(datetime.datetime.now().timestamp()) >= frozen_window_end:
            raise gl.vm.UserError("[EXPECTED] challenge window has expired")
        max_attempts = frozen_max_attempts
        if attempts >= max_attempts:
            raise gl.vm.UserError("[EXPECTED] challenge limit for this spend has been reached")
        challenge_id = int(self.challenge_count)
        bond = int(gl.message.value)
        expected = self.quote_bond(int(challenged_value), int(spend_id))
        if bond != expected:
            raise gl.vm.UserError("[EXPECTED] challenge bond must equal the frozen quote")
        evidence = self._validate_challenge_evidence(spend, evidence_json)
        self.challenge_state[u256(challenge_id)] = "open"
        self.challenge_spend[u256(challenge_id)] = u256(int(spend_id))
        self.challenge_bond[u256(challenge_id)] = u256(bond)
        self.challenge_challenger[u256(challenge_id)] = _addr(gl.message.sender_address)
        self.challenge_cause[u256(challenge_id)] = str(cause)[:240]
        self.challenge_evidence[u256(challenge_id)] = json.dumps(evidence, sort_keys=True)
        self.challenge_deadline[u256(challenge_id)] = u256(int(datetime.datetime.now().timestamp()) + int(policy["response_window_seconds"]))
        self.challenge_registration_deadline[u256(challenge_id)] = u256(int(datetime.datetime.now().timestamp()) + int(policy["response_window_seconds"]))
        self.challenge_registered[u256(challenge_id)] = u256(0)
        self.challenge_by_spend[u256(int(spend_id))] = u256(challenge_id)
        self.open_by_spend[u256(int(spend_id))] = u256(1)
        self.challenge_count = u256(challenge_id + 1)
        self.challenge_attempts_by_spend[u256(int(spend_id))] = u256(attempts + 1)
        self.challenge_window_end_by_spend[policy_key] = u256(frozen_window_end)
        self.challenge_max_attempts_by_spend[policy_key] = u256(max_attempts)
        gl.get_contract_at(self.court).emit(on="finalized").open_challenge(
            _addr(self.guard), int(spend_id), challenge_id, _addr(self.vault), str(cause), int(self.challenge_deadline[u256(challenge_id)]), int(self.challenge_registration_deadline[u256(challenge_id)]), self.challenge_evidence[u256(challenge_id)]
        )

    @gl.public.write
    def ack_challenge(self, challenge_id: int) -> None:
        """Record that the canonical Court has accepted the challenge case."""
        if gl.message.sender_address != self.court:
            raise gl.vm.UserError("[EXPECTED] only the bound court may acknowledge challenge registration")
        key = u256(int(challenge_id))
        if str(self.challenge_state.get(key, "")) != "open":
            raise gl.vm.UserError("[EXPECTED] challenge is not open")
        if int(self.challenge_registered.get(key, u256(0))) == 1:
            return
        registration_deadline = int(self.challenge_registration_deadline.get(key, u256(0)))
        if registration_deadline <= 0 or int(datetime.datetime.now().timestamp()) >= registration_deadline:
            raise gl.vm.UserError("[EXPECTED] challenge registration window has expired")
        self.challenge_registered[key] = u256(1)

    @gl.public.write
    def reconcile_open_challenge(self, challenge_id: int) -> None:
        key = u256(int(challenge_id))
        if str(self.challenge_state.get(key, "")) != "open":
            raise gl.vm.UserError("[EXPECTED] only open challenges can be reconciled")
        if int(self.challenge_registered.get(key, u256(0))) == 1:
            return
        registration_deadline = int(self.challenge_registration_deadline.get(key, u256(0)))
        if registration_deadline <= 0 or int(datetime.datetime.now().timestamp()) >= registration_deadline:
            raise gl.vm.UserError("[EXPECTED] challenge registration window has expired; expire it instead")
        spend_id = int(self.challenge_spend[key])
        gl.get_contract_at(self.court).emit(on="finalized").open_challenge(
            _addr(self.guard), spend_id, int(challenge_id), _addr(self.vault), str(self.challenge_cause[key]), int(self.challenge_deadline[key]), int(self.challenge_registration_deadline.get(key, u256(0))), self.challenge_evidence.get(key, "[]")
        )

    @gl.public.write
    def expire_unregistered_challenge(self, challenge_id: int) -> None:
        """Release a challenge hold if its Court registration never finalized."""
        key = u256(int(challenge_id))
        if str(self.challenge_state.get(key, "")) == "settled":
            settlement = self.challenge_settlement.get(key, "")
            if settlement != "" and str(json.loads(settlement).get("result", "")) == "registration_expired":
                return
            raise gl.vm.UserError("[EXPECTED] challenge is already settled")
        if str(self.challenge_state.get(key, "")) != "open":
            raise gl.vm.UserError("[EXPECTED] challenge is not open")
        if int(self.challenge_registered.get(key, u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] challenge registration is already acknowledged")
        deadline = int(self.challenge_registration_deadline.get(key, u256(0)))
        if deadline <= 0 or int(datetime.datetime.now().timestamp()) < deadline:
            raise gl.vm.UserError("[EXPECTED] challenge registration window is still open")
        spend_id = int(self.challenge_spend[key])
        self.open_by_spend[u256(spend_id)] = u256(0)
        bond = int(self.challenge_bond[key])
        challenger = Address(str(self.challenge_challenger[key]))
        self.challenge_settlement[key] = json.dumps({"result": "registration_expired", "restitution": 0, "reward": 0, "shortfall": 0}, sort_keys=True)
        self.challenge_state[key] = "settled"
        if bond > 0:
            _Payee(challenger).emit_transfer(value=u256(bond))
        # Court may have recorded the case even though this acknowledgment
        # never reached BondVault. Reconcile that record without authorizing a
        # late semantic result.
        gl.get_contract_at(self.court).emit(on="finalized").reconcile_expired_challenge(
            _addr(self.guard), int(challenge_id), _addr(gl.message.contract_address)
        )

    def _future_challenge_permitted(self, spend_id: int) -> bool:
        key = u256(int(spend_id))
        deadline = int(self.challenge_window_end_by_spend.get(key, u256(0)))
        if deadline <= 0:
            deadline = int(self.lock_deadline.get(key, u256(0)))
        if deadline <= 0 or int(datetime.datetime.now().timestamp()) >= deadline:
            return False
        attempts = int(self.challenge_attempts_by_spend.get(key, u256(0)))
        max_attempts = int(self.challenge_max_attempts_by_spend.get(key, u256(0)))
        if max_attempts <= 0:
            context = json.loads(str(gl.get_contract_at(self.guard).view().appeal_context(int(spend_id))))
            max_attempts = int(context["mandate"].get("challenge", {}).get("max_challenges", 2))
        return attempts < max_attempts

    @gl.public.write
    def settle(self, challenge_id: int, upheld: bool) -> None:
        if gl.message.sender_address != self.vault:
            raise gl.vm.UserError("[EXPECTED] only the bound vault may settle challenges")
        key = u256(int(challenge_id))
        state = str(self.challenge_state.get(key, ""))
        if state == "settled":
            settlement = self.challenge_settlement.get(key, "")
            if settlement != "" and str(json.loads(settlement).get("result", "")) == "registration_expired":
                raise gl.vm.UserError("[EXPECTED] expired challenge cannot be settled")
            if settlement != "":
                settled = json.loads(settlement)
                result = str(settled.get("result", ""))
                if result == "dismissed":
                    gl.get_contract_at(self.vault).emit(value=u256(int(self.challenge_bond[key])), on="finalized").receive_challenge_bond(int(challenge_id))
                elif result == "upheld":
                    restitution = int(settled.get("restitution", 0))
                    if restitution > 0:
                        gl.get_contract_at(self.vault).emit(value=u256(restitution), on="finalized").receive_reimbursement(int(challenge_id), restitution)
            return
        if state != "open":
            raise gl.vm.UserError("[EXPECTED] challenge is not open")
        if int(self.challenge_registered.get(key, u256(0))) != 1:
            raise gl.vm.UserError("[EXPECTED] challenge registration has not been acknowledged")
        bond = int(self.challenge_bond[key])
        challenger = Address(str(self.challenge_challenger[key]))
        spend_id = int(self.challenge_spend[key])
        spend = json.loads(str(gl.get_contract_at(self.guard).view().get_spend(spend_id)))
        amount = int(spend.get("amount", 0)) if bool(upheld) and bool(json.loads(str(gl.get_contract_at(self.vault).view().payment(spend_id))).get("paid", False)) else 0
        available = max(0, int(self.standing) - int(self.locked) + int(self.locked_by_spend.get(u256(spend_id), u256(0))))
        recovered = min(amount, available)
        bonus = 0
        locked_for_spend = int(self.locked_by_spend.get(u256(spend_id), u256(0)))
        keep_lock_for_retry = (not bool(upheld)) and self._future_challenge_permitted(spend_id)
        release_lock = not keep_lock_for_retry
        if bool(upheld):
            if _addr(self.vault) == _addr("0x0000000000000000000000000000000000000000"):
                raise gl.vm.UserError("[EXPECTED] vault binding is not initialized")
            self.standing = u256(int(self.standing) - recovered - bonus)
            if recovered > 0:
                gl.get_contract_at(self.vault).emit(value=u256(recovered), on="finalized").receive_reimbursement(int(challenge_id), recovered)
            if bond > 0:
                _Payee(challenger).emit_transfer(value=u256(bond))
            if bonus > 0:
                _Payee(challenger).emit_transfer(value=u256(bonus))
            self.challenger_losses[str(self.challenge_challenger[key])] = u256(0)
            self.challenge_settlement[key] = json.dumps({"result": "upheld", "restitution": recovered, "reward": bonus, "shortfall": amount - recovered, "lock_released": True, "future_challenges_remaining": False}, sort_keys=True)
            self.upheld_by_spend[u256(spend_id)] = u256(1)
        else:
            gl.get_contract_at(self.vault).emit(value=u256(bond), on="finalized").receive_challenge_bond(int(challenge_id))
            challenger_key = str(self.challenge_challenger[key])
            self.challenger_losses[challenger_key] = u256(int(self.challenger_losses.get(challenger_key, u256(0))) + 1)
            self.challenger_loss_at[challenger_key] = u256(int(datetime.datetime.now().timestamp()))
            self.challenge_settlement[key] = json.dumps({"result": "dismissed", "restitution": 0, "reward": 0, "shortfall": 0, "lock_released": release_lock, "future_challenges_remaining": keep_lock_for_retry}, sort_keys=True)
            self.open_by_spend[u256(spend_id)] = u256(0)
        self.open_by_spend[u256(spend_id)] = u256(0)
        if release_lock and locked_for_spend > 0:
            self.locked = u256(int(self.locked) - locked_for_spend)
            self.locked_by_spend[u256(spend_id)] = u256(0)
        self.challenge_state[key] = "settled"

    @gl.public.view
    def has_open_challenge(self, spend_id: int) -> bool:
        return int(self.open_by_spend.get(u256(int(spend_id)), u256(0))) == 1

    @gl.public.view
    def has_upheld_challenge(self, spend_id: int) -> bool:
        return int(self.upheld_by_spend.get(u256(int(spend_id)), u256(0))) == 1

    @gl.public.view
    def exposure_locked(self, spend_id: int) -> bool:
        return int(self.locked_by_spend.get(u256(int(spend_id)), u256(0))) > 0

    @gl.public.view
    def locked_amount(self, spend_id: int) -> int:
        return int(self.locked_by_spend.get(u256(int(spend_id)), u256(0)))

    @gl.public.view
    def status(self) -> str:
        return json.dumps({"charter": _addr(self.charter), "agent": _addr(self.agent), "guard": _addr(self.guard), "court": _addr(self.court), "vault": _addr(self.vault), "standing": int(self.standing), "locked": int(self.locked), "challenge_count": int(self.challenge_count)})

    @gl.public.view
    def challenge(self, challenge_id: int) -> str:
        key = u256(int(challenge_id))
        spend_id = int(self.challenge_spend.get(key, u256(0)))
        state = str(self.challenge_state.get(key, ""))
        future = self._future_challenge_permitted(spend_id) if state in ("open", "settled") else False
        return json.dumps({"id": int(challenge_id), "state": state, "spend_id": spend_id, "bond": int(self.challenge_bond.get(key, u256(0))), "challenger": str(self.challenge_challenger.get(key, "")), "cause": str(self.challenge_cause.get(key, "")), "evidence": json.loads(self.challenge_evidence.get(key, "[]")), "deadline": int(self.challenge_deadline.get(key, u256(0))), "registration_deadline": int(self.challenge_registration_deadline.get(key, u256(0))), "challenge_window_end": int(self.challenge_window_end_by_spend.get(u256(spend_id), u256(0))), "challenge_attempts": int(self.challenge_attempts_by_spend.get(u256(spend_id), u256(0))), "max_challenges": int(self.challenge_max_attempts_by_spend.get(u256(spend_id), u256(0))), "future_challenges_remaining": future, "registered": int(self.challenge_registered.get(key, u256(0))) == 1, "settlement": self.challenge_settlement.get(key, "")})

    @gl.public.view
    def info(self) -> str:
        return json.dumps({"charter": _addr(self.charter), "agent": _addr(self.agent), "guard": _addr(self.guard), "court": _addr(self.court), "vault": _addr(self.vault), "release": "steward-bond-vault/2"})
