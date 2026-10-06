# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import datetime
import hashlib
import json


def _addr(value) -> str:
    if hasattr(value, "as_hex"):
        return str(value.as_hex).lower()
    address = Address(str(value))
    return str(getattr(address, "as_hex", address)).lower()


def _is_sha256(value: str) -> bool:
    text = str(value).lower().strip()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def _key(charter: str, issuer: str, role: str, uri: str, digest: str) -> str:
    material = "|".join([_addr(charter), _addr(issuer), str(role), str(uri), str(digest).lower()])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class EvidenceRegistry(gl.Contract):
    """Historical issuer-wallet attestation for exact URI+digest evidence."""

    state: TreeMap[str, str]
    issuer_nonce: TreeMap[str, u256]

    def __init__(self):
        pass

    def _now(self) -> int:
        return int(datetime.datetime.now().timestamp())

    @gl.public.write
    def attest(self, charter: str, role: str, uri: str, digest: str) -> None:
        issuer = _addr(gl.message.sender_address)
        _ = Address(str(charter))
        if str(role).strip() == "" or str(uri).strip() == "":
            raise Exception("[EXPECTED] role and URI are required")
        if len(str(uri)) > 600:
            raise Exception("[EXPECTED] URI too long")
        if not _is_sha256(str(digest)):
            raise Exception("[EXPECTED] digest must be sha256 hex")
        k = _key(str(charter), issuer, str(role), str(uri), str(digest))
        if self.state.get(k, "") != "":
            raise Exception("[EXPECTED] this exact evidence identity already exists; history is immutable")
        nonce = int(self.issuer_nonce.get(issuer, u256(0))) + 1
        self.issuer_nonce[issuer] = u256(nonce)
        self.state[k] = json.dumps({
            "charter": _addr(str(charter)),
            "issuer": issuer,
            "role": str(role),
            "uri": str(uri),
            "digest": str(digest).lower(),
            "attested_at": self._now(),
            "revoked_at": 0,
            "issuer_nonce": nonce,
        })

    @gl.public.write
    def revoke(self, charter: str, role: str, uri: str, digest: str) -> None:
        issuer = _addr(gl.message.sender_address)
        k = _key(str(charter), issuer, str(role), str(uri), str(digest))
        raw = self.state.get(k, "")
        if raw == "":
            raise Exception("[EXPECTED] unknown attestation")
        record = json.loads(raw)
        if int(record.get("revoked_at", 0)) != 0:
            raise Exception("[EXPECTED] attestation already revoked")
        record["revoked_at"] = self._now()
        self.state[k] = json.dumps(record)

    @gl.public.view
    def status_at(self, charter: str, issuer: str, role: str, uri: str, digest: str, at: int) -> bool:
        raw = self.state.get(_key(str(charter), str(issuer), str(role), str(uri), str(digest)), "")
        if raw == "":
            return False
        record = json.loads(raw)
        stamp = int(at)
        attested = int(record.get("attested_at", 0))
        revoked = int(record.get("revoked_at", 0))
        return attested > 0 and attested <= stamp and (revoked == 0 or revoked > stamp)

    @gl.public.view
    def attestation(self, charter: str, issuer: str, role: str, uri: str, digest: str) -> str:
        return self.state.get(_key(str(charter), str(issuer), str(role), str(uri), str(digest)), "")

    @gl.public.view
    def nonce_of(self, issuer: str) -> int:
        return int(self.issuer_nonce.get(_addr(str(issuer)), u256(0)))
