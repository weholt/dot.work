import json
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def gold_dir() -> Path:
    return Path(__file__).parent / "gold"


@pytest.fixture
def tmp_output_dir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="kgtool_tests_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def enterprise_doc(data_dir: Path) -> Path:
    return data_dir / "enterprise_architecture_spec.md"


@pytest.fixture
def sample_doc(data_dir: Path) -> Path:
    return data_dir / "sample_spec.md"


@pytest.fixture
def chaotic_doc(data_dir: Path) -> Path:
    return data_dir / "chaotic_mess.md"


@pytest.fixture
def extreme_doc(data_dir: Path) -> Path:
    return data_dir / "extreme_stress_test.md"


@pytest.fixture
def topic_terms_enterprise(gold_dir: Path) -> dict:
    path = gold_dir / "topic_terms_enterprise.json"
    return json.loads(path.read_text(encoding="utf-8"))
