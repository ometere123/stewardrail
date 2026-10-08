from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[2]
CONTRACTS=ROOT/'contracts'


def text(name): return (CONTRACTS/name).read_text()


def test_exactly_five_deployable_contracts_and_no_generated_build_tree():
    names=sorted(p.name for p in CONTRACTS.glob('*.py'))
    assert names==sorted(['steward_charter.py','evidence_registry.py','steward_guard.py','steward_court.py','steward_vault.py','steward_bond_vault.py'])
    assert not (CONTRACTS/'build').exists()
    assert not list(CONTRACTS.rglob('*.min.py'))


def test_guard_never_moves_value():
    s=text('steward_guard.py')
    assert 'emit_transfer' not in s and '@gl.public.write.payable' not in s


def test_vault_is_only_treasury_payout_surface():
    for n in ['steward_charter.py','evidence_registry.py','steward_guard.py']:
        assert 'emit_transfer' not in text(n)
    assert 'emit_transfer' in text('steward_vault.py')


def test_jury_fetch_is_independent_in_leader_and_validator():
    for n in ['steward_guard.py','steward_court.py']:
        s=text(n)
        assert s.count('gl.nondet.web.get') >= 2
        assert 'gl.vm.run_nondet' in s


def test_no_principal_semantic_override():
    s=text('steward_guard.py').lower()
    assert 'override_release' not in s and 'override_refuse' not in s


def test_court_has_bidirectional_reversal_logic():
    s=text('steward_court.py')
    assert 'record["effective"] = str(result["verdict"])' in s and 'record["effective"] = str(result["verdict"])' in s


def test_contract_cross_calls_stay_outside_nondet_closures():
    # Crude but useful regression guard: closure bodies must not call get_contract_at.
    for n in ['steward_guard.py','steward_court.py']:
        s=text(n)
        for marker in ['def leader()', 'def validator(']:
            start=s.index(marker)
            end=s.find('\n    @gl.public.write', start)
            if end == -1:
                end = len(s)
            assert 'gl.get_contract_at' not in s[start:end]


def test_user_facing_rejections_use_genvm_user_error():
    for path in CONTRACTS.glob('*.py'):
        source = path.read_text()
        assert 'raise Exception(' not in source, path.name
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call):
                continue
            called = ast.unparse(node.exc.func)
            assert called != 'Exception', f'{path.name}:{node.lineno} uses bare Exception'


def test_sdk_addresses_are_never_stringified_before_normalization():
    forbidden = (
        'str(Address(',
        'str(gl.message.sender_address)',
        'str(gl.message.contract_address)',
        'str(self.agent)',
        'str(self.charter)',
        'str(self.registry)',
        'str(self.court)',
        'str(self.guard)',
    )
    for path in CONTRACTS.glob('*.py'):
        source = path.read_text()
        for marker in forbidden:
            assert marker not in source, f'{path.name} reintroduced unsafe address serialization: {marker}'
        assert 'getattr(address, "as_hex", address)' in source, path.name
