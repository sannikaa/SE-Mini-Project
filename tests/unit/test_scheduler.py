import pytest
from ctgs.constraints import validate_timetable
from ctgs.models import DAYS
from ctgs.scheduler import (InvalidDatasetError, SchedulingError,
                            build_sessions, generate)


def test_tc_s01_build_sessions_counts_and_lab_first(tiny_ds):
    sessions = build_sessions(tiny_ds)
    assert len(sessions) == 3 + 1 + 3          # S1: 3 theory + 1 lab block, S2: 3 theory
    assert sessions[0][2] == 2                  # lab block sorted first


def test_tc_s02_generate_valid_timetable(tiny_ds):
    entries = generate(tiny_ds)
    assert sum(e.length for e in entries) == 3 + 2 + 3
    assert validate_timetable(entries, tiny_ds) == []


def test_tc_s03_generate_spreads_theory_across_days(tiny_ds):
    entries = generate(tiny_ds)
    days = {e.day for e in entries if e.section_id == "S1" and e.course_code == "C1"}
    assert len(days) == 3


def test_tc_s04_invalid_dataset_rejected(tiny_data):
    from ctgs.models import Dataset
    tiny_data["courses"][0]["faculty_id"] = "NOPE"
    with pytest.raises(InvalidDatasetError) as exc:
        generate(Dataset.from_dict(tiny_data))
    assert exc.value.errors


def test_tc_s05_infeasible_dataset_raises(tiny_data):
    from ctgs.models import Dataset
    tiny_data["faculty"][0]["unavailable"] = [[d, p] for d in DAYS for p in range(1, 7)]
    with pytest.raises(SchedulingError, match="No feasible"):
        generate(Dataset.from_dict(tiny_data))


def test_tc_s06_step_limit_raises(tiny_ds):
    with pytest.raises(SchedulingError, match="Step limit"):
        generate(tiny_ds, max_steps=1)


def test_tc_s07_sample_dataset_schedules_cleanly(sample_path):
    from ctgs.io_utils import load_dataset
    ds = load_dataset(sample_path)
    assert validate_timetable(generate(ds), ds) == []
