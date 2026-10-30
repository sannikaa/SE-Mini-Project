import copy
from pathlib import Path
import pytest
from ctgs.models import Dataset

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_dataset.json"

TINY = {
    "faculty": [{"id": "F1", "name": "A", "unavailable": [["Mon", 1]]},
                {"id": "F2", "name": "B"}],
    "rooms": [{"id": "R1", "capacity": 60}, {"id": "L1", "capacity": 60, "is_lab": True}],
    "courses": [
        {"code": "C1", "name": "Theory", "hours_per_week": 3, "faculty_id": "F1"},
        {"code": "C2L", "name": "Lab", "hours_per_week": 2, "faculty_id": "F2", "is_lab": True}],
    "sections": [{"id": "S1", "strength": 50, "courses": ["C1", "C2L"]},
                 {"id": "S2", "strength": 40, "courses": ["C1"]}],
}


@pytest.fixture
def tiny_data():
    return copy.deepcopy(TINY)


@pytest.fixture
def tiny_ds(tiny_data):
    return Dataset.from_dict(tiny_data)


@pytest.fixture
def sample_path():
    return str(SAMPLE)
