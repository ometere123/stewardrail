"""Direct-Mode-oriented structural tests that run even without genlayer-test.

The live Direct Mode suite is intentionally separated: CI/source review can
still catch architecture regressions in a plain Python environment, while
scripts/direct_mode.py runs actual genlayer-test when the GenLayer toolchain is
installed.
"""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def parsed(name): return ast.parse((ROOT/'contracts'/name).read_text())


def class_names(name): return [n.name for n in ast.walk(parsed(name)) if isinstance(n,ast.ClassDef)]


def test_contract_class_names_are_stable():
    expected={
      'steward_charter.py':'StewardCharter','evidence_registry.py':'EvidenceRegistry',
      'steward_guard.py':'StewardGuard','steward_court.py':'StewardCourt','steward_vault.py':'StewardVault'}
    expected['steward_bond_vault.py']='StewardBondVault'
    for file, cls in expected.items(): assert cls in class_names(file)


def test_sources_are_syntax_valid():
    for p in (ROOT/'contracts').glob('*.py'): ast.parse(p.read_text())
