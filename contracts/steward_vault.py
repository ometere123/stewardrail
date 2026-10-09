# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

ALLOW = "allow"
REFUSE = "refuse"


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


class StewardVault(gl.Contract):
    """Custody rail. It only sees terminal decisions delivered by a finalized court transaction."""

    charter: Address
    guard: Address
    court: Address
    bond_vault: Address
    treasury: u256
    funded: u256
    paid_total: u256
    recovery_nonce: u256
    terminal: TreeMap[u256, str]
    paid: TreeMap[u256, u256]
    challenge_outcome: TreeMap[u256, str]
    latest_challenge: TreeMap[u256, u256]

    def __init__(self, charter: str, guard: str, court: str, bond_vault: str):
        self.charter = Address(str(charter))
        self.guard = Address(str(guard))
        self.court = Address(str(court))
        self.bond_vault = Address(str(bond_vault))
        guard_info = json.loads(str(gl.get_contract_at(self.guard).view().info()))
        court_info = json.loads(str(gl.get_contract_at(self.court).view().info()))
        if _addr(guard_info["charter"]) != _addr(self.charter) or _addr(guard_info["court"]) != _addr(self.court):
            raise gl.vm.UserError("[EXPECTED] guard binding mismatch")
        if _addr(court_info["charter"]) != _addr(self.charter):
            raise gl.vm.UserError("[EXPECTED] court binding mismatch")
        self.treasury = u256(0)
        self.funded = u256(0)
        self.paid_total = u256(0)
        self.recovery_nonce = u256(0)

    @gl.public.write.payable
    def fund(self) -> None:
        value = int(gl.message.value)
        if value <= 0:
            raise gl.vm.UserError("[EXPECTED] funding value must be positive")
        self.treasury = u256(int(self.treasury) + value)
        self.funded = u256(int(self.funded) + value)

    @gl.public.write.payable
    def receive_reimbursement(self) -> None:
        if gl.message.sender_address != self.bond_vault:
            raise gl.vm.UserError("[EXPECTED] only the bound collateral vault may reimburse treasury")
        value = int(gl.message.value)
        if value <= 0:
            raise gl.vm.UserError("[EXPECTED] reimbursement must be positive")
        self.treasury = u256(int(self.treasury) + value)
        self.funded = u256(int(self.funded) + value)

    @gl.public.write
    def record_terminal(self, guard: str, spend_id: int, decision: str, amount: int, recipient: str) -> None:
        if gl.message.sender_address != self.guard:
            raise gl.vm.UserError("[EXPECTED] only the bound guard may record terminal economic decisions")
        if _addr(guard) != _addr(self.guard) or str(decision) not in (ALLOW, REFUSE) or int(amount) <= 0:
            raise gl.vm.UserError("[EXPECTED] invalid terminal decision")
        key = u256(int(spend_id))
        incoming = json.dumps({"decision": str(decision), "amount": int(amount), "recipient": _addr(str(recipient))}, sort_keys=True)
        existing = self.terminal.get(key, "")
        if existing != "":
            if existing == incoming:
                return
            raise gl.vm.UserError("[EXPECTED] conflicting terminal decision")
        self.terminal[key] = incoming

    @gl.public.write
    def apply_challenge_result(self, challenge_id: int, spend_id: int, upheld: bool, bond_vault: str) -> None:
        if gl.message.sender_address != self.guard:
            raise gl.vm.UserError("[EXPECTED] only the bound guard may apply challenge outcomes")
        if _addr(str(bond_vault)) != _addr(self.bond_vault):
            raise gl.vm.UserError("[EXPECTED] challenge collateral binding mismatch")
        info = json.loads(str(gl.get_contract_at(self.bond_vault).view().info()))
        if _addr(info.get("guard", "")) != _addr(self.guard) or _addr(info.get("vault", "")) != _addr(gl.message.contract_address):
            raise gl.vm.UserError("[EXPECTED] challenge collateral is not bound to this vault")
        challenge = json.loads(str(gl.get_contract_at(self.bond_vault).view().challenge(int(challenge_id))))
        if int(challenge.get("spend_id", -1)) != int(spend_id):
            raise gl.vm.UserError("[EXPECTED] challenge identity does not match spend")
        key = u256(int(challenge_id))
        incoming = json.dumps({"challenge_id": int(challenge_id), "upheld": bool(upheld)}, sort_keys=True)
        existing = self.challenge_outcome.get(key, "")
        if existing != "" and existing != incoming:
            raise gl.vm.UserError("[EXPECTED] conflicting challenge outcome")
        self.challenge_outcome[key] = incoming
        self.latest_challenge[u256(int(spend_id))] = u256(int(challenge_id))
        gl.get_contract_at(self.bond_vault).emit(on="finalized").settle(int(challenge_id), bool(upheld))

    @gl.public.write
    def pay(self, spend_id: int) -> None:
        key = u256(int(spend_id))
        if int(self.paid.get(key, u256(0))) == 1:
            raise gl.vm.UserError("[EXPECTED] spend already paid")
        raw = self.terminal.get(key, "")
        if raw == "":
            raise gl.vm.UserError("[EXPECTED] no protocol-final terminal decision has reached the vault")
        record = json.loads(raw)
        if str(record["decision"]) != ALLOW:
            raise gl.vm.UserError("[EXPECTED] terminal decision refuses payment")
        if bool(gl.get_contract_at(self.guard).view().is_revoked(int(spend_id))):
            raise gl.vm.UserError("[EXPECTED] terminal authorization has been revoked")
        if bool(gl.get_contract_at(self.bond_vault).view().has_open_challenge(int(spend_id))):
            raise gl.vm.UserError("[EXPECTED] an open challenge blocks payment")
        if bool(gl.get_contract_at(self.bond_vault).view().has_upheld_challenge(int(spend_id))):
            raise gl.vm.UserError("[EXPECTED] upheld challenge blocks payment")
        amount = int(record["amount"])
        if amount > int(self.treasury):
            raise gl.vm.UserError("[EXPECTED] insufficient treasury")
        self.paid[key] = u256(1)
        self.treasury = u256(int(self.treasury) - amount)
        self.paid_total = u256(int(self.paid_total) + amount)
        _Payee(Address(str(record["recipient"]))).emit_transfer(value=u256(amount))

    @gl.public.write
    def recover(self, to: str, amount: int) -> None:
        value = int(amount)
        if value <= 0 or value > int(self.treasury):
            raise gl.vm.UserError("[EXPECTED] invalid recovery amount")
        nonce = int(self.recovery_nonce)
        approved = bool(gl.get_contract_at(self.charter).view().recovery_is_approved(_addr(gl.message.contract_address), str(to), value, nonce))
        if not approved:
            raise gl.vm.UserError("[EXPECTED] charter threshold has not approved this recovery")
        self.recovery_nonce = u256(nonce + 1)
        self.treasury = u256(int(self.treasury) - value)
        _Payee(Address(str(to))).emit_transfer(value=u256(value))

    @gl.public.view
    def payment(self, spend_id: int) -> str:
        key = u256(int(spend_id))
        raw = self.terminal.get(key, "")
        challenge_id = int(self.latest_challenge.get(key, u256(0)))
        return json.dumps({
            "spend_id": int(spend_id), "terminal": None if raw == "" else json.loads(raw),
            "paid": int(self.paid.get(key, u256(0))) == 1,
            "challenge_id": challenge_id,
            "challenge": None if self.challenge_outcome.get(u256(challenge_id), "") == "" else json.loads(self.challenge_outcome[u256(challenge_id)]),
        })

    @gl.public.view
    def challenge_outcome_for(self, challenge_id: int) -> str:
        raw = self.challenge_outcome.get(u256(int(challenge_id)), "")
        return raw if raw != "" else "{}"

    @gl.public.write.payable
    def receive_challenge_bond(self, challenge_id: int) -> None:
        if gl.message.sender_address != self.bond_vault:
            raise gl.vm.UserError("[EXPECTED] only the bound collateral vault may return a dismissed bond")
        if int(gl.message.value) <= 0:
            raise gl.vm.UserError("[EXPECTED] challenge bond must be positive")
        if self.challenge_outcome.get(u256(int(challenge_id)), "") == "":
            raise gl.vm.UserError("[EXPECTED] challenge outcome is not recorded")
        self.treasury = u256(int(self.treasury) + int(gl.message.value))
        self.funded = u256(int(self.funded) + int(gl.message.value))

    @gl.public.view
    def status(self) -> str:
        return json.dumps({
            "charter": _addr(self.charter), "guard": _addr(self.guard), "court": _addr(self.court), "bond_vault": _addr(self.bond_vault),
            "treasury": int(self.treasury), "funded": int(self.funded), "paid_total": int(self.paid_total),
            "recovery_nonce": int(self.recovery_nonce), "release": "steward-vault/1",
        })

    @gl.public.view
    def info(self) -> str:
        return json.dumps({"charter": _addr(self.charter), "guard": _addr(self.guard), "court": _addr(self.court), "bond_vault": _addr(self.bond_vault), "release": "steward-vault/2"})
