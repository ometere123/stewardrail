#!/usr/bin/env python3
"""Run the official genlayer-test Direct Mode suite for exact contract sources.

The distribution is named ``genlayer-test`` but its public Python package is
``gltest``.  The adversarial in-memory harness intentionally remains part of
the normal pytest suite; this runner selects only tests that use the official
Direct Mode fixtures.
"""
import importlib.util
import os
import subprocess
import sys

if importlib.util.find_spec("gltest") is None:
    print("gltest is not installed. Install genlayer-test==0.29.2, then rerun.", file=sys.stderr)
    raise SystemExit(2)

environment = dict(os.environ)
environment["STEWARDRAIL_RUN_DIRECT"] = "1"
raise SystemExit(subprocess.call([
    sys.executable, "-m", "pytest", "tests/direct/test_genlayer_direct_mode.py",
    "-q",
], env=environment))
