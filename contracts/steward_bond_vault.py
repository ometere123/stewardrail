# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import datetime
import json


def _addr(value) -> str:
    if hasattr(value, "as_hex"):
        return str(value.as_hex).lower()
    address = Address(str(value))
    return str(getattr(address, "as_hex", address)).lower()


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
    vault: Address
    standing: u256
    locked: u256
    challenge_count: u256
    challenge_state: TreeMap[u256, str]
    challenge_spend: TreeMap[u256, u256]
    challenge_bond: TreeMap[u256, u256]
    challenge_challenger: TreeMap[u256, str]
    challenge_settlement: TreeMap[u256, str]
    challenger_losses: TreeMap[str, u256]
    challenger_loss_at: TreeMap[str, u256]

    def __init__(self, charter: str, agent: str):
        self.charter = Address(str(charter))
        info = json.loads(str(gl.get_contract_at(self.charter).view().current()))
        self.agent = Address(str(agent))
        if _addr(info["agent"]) != _addr(self.agent):
            raise gl.vm.UserError("[EXPECTED] collateral agent does not match charter")
        self.guard = Address("0x0000000000000000000000000000000000000000")
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
    def lock_exposure(self, amount: int) -> None:
        if gl.message.sender_address != self.guard:
            raise gl.vm.UserError("[EXPECTED] only the bound guard may lock standing exposure")
        value = int(amount)
        if value <= 0 or int(self.standing) - int(self.locked) < value:
            raise gl.vm.UserError("[EXPECTED] insufficient available standing collateral")
        self.locked = u256(int(self.locked) + value)

    @gl.public.write
    def release_exposure(self, amount: int) -> None:
        if gl.message.sender_address != self.guard:
            raise gl.vm.UserError("[EXPECTED] only the bound guard may release standing exposure")
        value = int(amount)
        if value <= 0 or value > int(self.locked):
            raise gl.vm.UserError("[EXPECTED] invalid standing exposure release")
        self.locked = u256(int(self.locked) - value)

    @gl.public.view
    def quote_bond(self, challenged_value: int) -> int:
        value = int(challenged_value)
        if value <= 0:
            raise gl.vm.UserError("[EXPECTED] challenged value must be positive")
        mandate = json.loads(str(gl.get_contract_at(self.charter).view().current()))["mandate"]
        policy = json.loads(str(mandate))["challenge"]
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
    def open_challenge(self, spend_id: int, challenged_value: int, cause: str) -> None:
        if _addr(self.guard) == _addr("0x0000000000000000000000000000000000000000"):
            raise gl.vm.UserError("[EXPECTED] collateral bindings are not initialized")
        if gl.message.sender_address == self.agent:
            raise gl.vm.UserError("[EXPECTED] agent cannot challenge its own authorization")
        if len(str(cause).strip()) == 0 or len(str(cause)) > 240:
            raise gl.vm.UserError("[EXPECTED] challenge cause is invalid")
        spend = json.loads(str(gl.get_contract_at(self.guard).view().get_spend(int(spend_id))))
        if int(spend.get("amount", 0)) != int(challenged_value) or str(spend.get("terminal_economic", "")) != "allow":
            raise gl.vm.UserError("[EXPECTED] spend is not challengeable")
        policy = json.loads(str(gl.get_contract_at(self.charter).view().current()))["mandate"]
        policy = json.loads(str(policy))["challenge"]
        if int(datetime.datetime.now().timestamp()) > int(spend.get("requested_at", 0)) + int(policy["window_seconds"]):
            raise gl.vm.UserError("[EXPECTED] challenge window has expired")
        i = 0
        while i < int(self.challenge_count):
            existing = u256(i)
            if int(self.challenge_spend.get(existing, u256(0))) == int(spend_id) and str(self.challenge_state.get(existing, "")) == "open":
                raise gl.vm.UserError("[EXPECTED] an open challenge already exists")
            i += 1
        challenge_id = int(self.challenge_count)
        bond = int(gl.message.value)
        expected = self.quote_bond(int(challenged_value))
        if bond <= 0 or bond < expected:
            raise gl.vm.UserError("[EXPECTED] challenge bond must be positive")
        self.challenge_state[u256(challenge_id)] = "open"
        self.challenge_spend[u256(challenge_id)] = u256(int(spend_id))
        self.challenge_bond[u256(challenge_id)] = u256(bond)
        self.challenge_challenger[u256(challenge_id)] = _addr(gl.message.sender_address)
        self.challenge_count = u256(challenge_id + 1)

    @gl.public.write
    def settle(self, challenge_id: int, upheld: bool, restitution: int, reward: int) -> None:
        if gl.message.sender_address != self.guard:
            raise gl.vm.UserError("[EXPECTED] only the bound guard may settle challenges")
        key = u256(int(challenge_id))
        state = str(self.challenge_state.get(key, ""))
        if state == "settled":
            return
        if state != "open":
            raise gl.vm.UserError("[EXPECTED] challenge is not open")
        bond = int(self.challenge_bond[key])
        challenger = Address(str(self.challenge_challenger[key]))
        amount = int(restitution)
        bonus = int(reward)
        if amount < 0 or bonus < 0 or amount + bonus > int(self.standing):
            raise gl.vm.UserError("[EXPECTED] settlement exceeds standing collateral")
        if bool(upheld):
            if _addr(self.vault) == _addr("0x0000000000000000000000000000000000000000"):
                raise gl.vm.UserError("[EXPECTED] vault binding is not initialized")
            self.standing = u256(int(self.standing) - amount - bonus)
            if amount > 0:
                gl.get_contract_at(self.vault).emit(on="finalized").receive_reimbursement(value=u256(amount))
            if bond > 0:
                _Payee(challenger).emit_transfer(value=u256(bond))
            if bonus > 0:
                _Payee(challenger).emit_transfer(value=u256(bonus))
            self.challenger_losses[str(self.challenge_challenger[key])] = u256(0)
            self.challenge_settlement[key] = json.dumps({"result": "upheld", "restitution": amount, "reward": bonus, "shortfall": 0}, sort_keys=True)
        else:
            if _addr(self.vault) == _addr("0x0000000000000000000000000000000000000000"):
                raise gl.vm.UserError("[EXPECTED] vault binding is not initialized")
            _Payee(self.vault).emit_transfer(value=u256(bond))
            challenger_key = str(self.challenge_challenger[key])
            self.challenger_losses[challenger_key] = u256(int(self.challenger_losses.get(challenger_key, u256(0))) + 1)
            self.challenger_loss_at[challenger_key] = u256(int(datetime.datetime.now().timestamp()))
            self.challenge_settlement[key] = json.dumps({"result": "dismissed", "restitution": 0, "reward": 0, "shortfall": 0}, sort_keys=True)
        self.challenge_state[key] = "settled"

    @gl.public.view
    def has_open_challenge(self, spend_id: int) -> bool:
        i = 0
        while i < int(self.challenge_count):
            key = u256(i)
            if int(self.challenge_spend.get(key, u256(0))) == int(spend_id) and str(self.challenge_state.get(key, "")) == "open":
                return True
            i += 1
        return False

    @gl.public.view
    def has_upheld_challenge(self, spend_id: int) -> bool:
        i = 0
        while i < int(self.challenge_count):
            key = u256(i)
            if int(self.challenge_spend.get(key, u256(0))) == int(spend_id) and '"result": "upheld"' in str(self.challenge_settlement.get(key, "")):
                return True
            i += 1
        return False

    @gl.public.view
    def status(self) -> str:
        return json.dumps({"charter": _addr(self.charter), "agent": _addr(self.agent), "guard": _addr(self.guard), "vault": _addr(self.vault), "standing": int(self.standing), "locked": int(self.locked), "challenge_count": int(self.challenge_count)})

    @gl.public.view
    def challenge(self, challenge_id: int) -> str:
        key = u256(int(challenge_id))
        return json.dumps({"id": int(challenge_id), "state": str(self.challenge_state.get(key, "")), "spend_id": int(self.challenge_spend.get(key, u256(0))), "bond": int(self.challenge_bond.get(key, u256(0))), "challenger": str(self.challenge_challenger.get(key, "")), "settlement": self.challenge_settlement.get(key, "")})

    @gl.public.view
    def info(self) -> str:
        return json.dumps({"charter": _addr(self.charter), "agent": _addr(self.agent), "guard": _addr(self.guard), "vault": _addr(self.vault), "release": "steward-bond-vault/1"})
