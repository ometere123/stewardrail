"""Keep the official Direct Mode runtime isolated from the CI source harness."""
import os

import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("STEWARDRAIL_RUN_DIRECT") == "1":
        return
    skip_direct_runtime = pytest.mark.skip(
        reason="run official Direct Mode explicitly with python scripts/direct_mode.py",
    )
    for item in items:
        if "direct" in item.keywords and "test_genlayer_direct_mode.py" in str(item.fspath):
            item.add_marker(skip_direct_runtime)
