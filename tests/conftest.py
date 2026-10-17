"""Shared pytest setup for the Phase 3 scenario tests.

Puts <repo>/src on sys.path so `from scenario.demand import fit_od` and
`from scenario.generator import build_scenario, default_params` work.
Per-test scratch directories come from pytest's built-in `tmp_path`.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: statistical or rebuild test that takes tens of seconds"
    )


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT
