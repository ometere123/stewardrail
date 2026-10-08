"""Official genlayer-test 0.29.2 Direct Mode checks.

These tests load the readable deployment inputs through the Direct Mode SDK
loader; they are deliberately distinct from the repository's adversarial
in-memory harness.  They provide a fast compatibility gate for the two
independent roots of the five-contract graph (Charter and Registry).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.direct

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _windows_gltest_tempfile_compat(monkeypatch):
    """Work around genlayer-test 0.29.2's open-tempfile unlink on Windows.

    The Direct Mode loader duplicates its message tempfile onto fd 0 and then
    unlinks it before the duplicate closes. Windows correctly rejects that
    unlink while POSIX permits it. Keeping the short-lived temp file is limited
    to this test process and lets the official runner exercise the real SDK.
    """
    if os.name != "nt":
        return
    original_unlink = os.unlink

    def unlink(path, *args, **kwargs):
        try:
            return original_unlink(path, *args, **kwargs)
        except PermissionError:
            return None

    monkeypatch.setattr(os, "unlink", unlink)


def _address(account) -> str:
    """Use the SDK address representation as canonical contract input."""
    if isinstance(account, bytes):
        return "0x" + account.hex()
    return str(getattr(account, "as_hex", account))


def _mandate(issuer: str) -> str:
    return json.dumps({
        "name": "Direct Mode shared treasury",
        "deterministic": {
            "max_per_spend": 1000,
            "rolling_limit": {"seconds": 3600, "amount": 2000},
            "category_allowlist": ["ops"],
            "recipient_denylist": [],
        },
        "semantic_rules": [{
            "id": "invoice-fit",
            "question": "Does the authenticated invoice satisfy the frozen mandate?",
            "when": {"type": "amount_gte", "value": 100},
            "evidence_roles": ["invoice"],
        }],
        "issuers": [{
            "address": issuer,
            "role": "invoice",
            "origins": ["https://issuer.example"],
        }],
        "appeal": {"window_seconds": 60, "bond": 0},
    })


def test_charter_threshold_and_duplicate_approval_direct_mode(direct_vm, direct_deploy, direct_accounts):
    alice, bob, agent, issuer = direct_accounts[:4]
    direct_vm.sender = alice
    charter = direct_deploy(
        ROOT / "contracts" / "steward_charter.py",
        json.dumps([_address(alice), _address(bob)]), 2, _address(agent), _mandate(_address(issuer)),
    )

    proposal = _mandate(_address(issuer))
    charter.approve_mandate(proposal)
    assert json.loads(charter.current())["version"] == 0
    with direct_vm.prank(alice), direct_vm.expect_revert("already approved"):
        charter.approve_mandate(proposal)
    with direct_vm.prank(bob):
        charter.approve_mandate(proposal)
    current = json.loads(charter.current())
    assert current["version"] == 1
    assert json.loads(charter.mandate_at(1))["name"] == "Direct Mode shared treasury"
    assert current["agent"] == _address(agent).lower()
    assert current["principals"] == [_address(alice).lower(), _address(bob).lower()]


def test_charter_expected_user_errors_direct_mode(direct_vm, direct_deploy, direct_accounts):
    alice, bob, outsider, agent, issuer = direct_accounts[:5]
    direct_vm.sender = alice
    charter = direct_deploy(
        ROOT / "contracts" / "steward_charter.py",
        json.dumps([_address(alice), _address(bob)]), 2, _address(agent), _mandate(_address(issuer)),
    )

    with direct_vm.prank(outsider), direct_vm.expect_revert("caller is not a charter principal"):
        charter.approve_mandate(_mandate(_address(issuer)))
    with direct_vm.expect_revert("mandate must be valid JSON"):
        charter.approve_mandate("not-json")
    with direct_vm.expect_revert("unknown mandate version"):
        charter.mandate_at(1)


def test_charter_recovery_requires_threshold_and_rejects_duplicate_direct_mode(direct_vm, direct_deploy, direct_accounts):
    alice, bob, agent, issuer, vault, recipient = direct_accounts[:6]
    direct_vm.sender = alice
    charter = direct_deploy(
        ROOT / "contracts" / "steward_charter.py",
        json.dumps([_address(alice), _address(bob)]), 2, _address(agent), _mandate(_address(issuer)),
    )

    charter.approve_recovery(_address(vault), _address(recipient), 25, 0)
    assert not charter.recovery_is_approved(_address(vault), _address(recipient), 25, 0)
    with direct_vm.expect_revert("already approved this recovery"):
        charter.approve_recovery(_address(vault), _address(recipient), 25, 0)
    with direct_vm.prank(bob):
        charter.approve_recovery(_address(vault), _address(recipient), 25, 0)
    assert charter.recovery_is_approved(_address(vault), _address(recipient), 25, 0)


def test_registry_historical_attestation_and_revocation_direct_mode(direct_vm, direct_deploy, direct_accounts):
    issuer, other, charter = direct_accounts[:3]
    registry = direct_deploy(ROOT / "contracts" / "evidence_registry.py")
    uri = "https://issuer.example/invoice/1"
    digest = "a" * 64

    with direct_vm.prank(issuer):
        registry.attest(_address(charter), "invoice", uri, digest)
    record = json.loads(registry.attestation(_address(charter), _address(issuer), "invoice", uri, digest))
    assert registry.status_at(_address(charter), _address(issuer), "invoice", uri, digest, record["attested_at"])
    with direct_vm.prank(other), direct_vm.expect_revert("unknown attestation"):
        registry.revoke(_address(charter), "invoice", uri, digest)
    # A later block timestamp is necessary to test the historical boundary;
    # timestamp-only provenance cannot order two writes in the same second.
    direct_vm.warp("2030-01-01T00:00:00Z")
    with direct_vm.prank(issuer):
        registry.revoke(_address(charter), "invoice", uri, digest)
    revoked = json.loads(registry.attestation(_address(charter), _address(issuer), "invoice", uri, digest))
    assert registry.status_at(_address(charter), _address(issuer), "invoice", uri, digest, record["attested_at"])
    assert not registry.status_at(_address(charter), _address(issuer), "invoice", uri, digest, revoked["revoked_at"])


def test_registry_expected_user_errors_and_immutable_identity_direct_mode(direct_vm, direct_deploy, direct_accounts):
    issuer, charter = direct_accounts[:2]
    direct_vm.sender = issuer
    registry = direct_deploy(ROOT / "contracts" / "evidence_registry.py")
    uri = "https://issuer.example/invoice/2"
    digest = "b" * 64

    with direct_vm.expect_revert("digest must be sha256 hex"):
        registry.attest(_address(charter), "invoice", uri, "not-a-digest")
    registry.attest(_address(charter), "invoice", uri, digest)
    with direct_vm.expect_revert("history is immutable"):
        registry.attest(_address(charter), "invoice", uri, digest)
    registry.revoke(_address(charter), "invoice", uri, digest)
    with direct_vm.expect_revert("already revoked"):
        registry.revoke(_address(charter), "invoice", uri, digest)


def test_charter_accepts_cli_native_json_values_direct_mode(direct_vm, direct_deploy, direct_accounts):
    alice, bob, agent, issuer = direct_accounts[:4]
    direct_vm.sender = alice
    mandate = json.loads(_mandate(_address(issuer)))
    charter = direct_deploy(
        ROOT / "contracts" / "steward_charter.py",
        [_address(alice), _address(bob)], 2, _address(agent), mandate,
    )
    charter.approve_mandate(mandate)
    with direct_vm.prank(bob):
        charter.approve_mandate(mandate)
    assert json.loads(charter.current())["version"] == 1
