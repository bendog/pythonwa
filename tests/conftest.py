import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT / "tests"))

# ==============================================
# Fixtures
# ==============================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def path_tests(project_root) -> Path:
    return project_root / "tests"


@pytest.fixture(scope="session")
def path_apis(project_root) -> Path:
    return project_root / "apis"
