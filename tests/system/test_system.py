"""System validation: end-to-end checks using independent oracles (not the app's own validator)."""
import json
from collections import defaultdict
import pytest
from ctgs.app import create_app
from ctgs.cli import main
from ctgs.constraints import validate_timetable
from ctgs.io_utils import load_dataset, load_timetable


@pytest.fixture
def generated(sample_path, tmp_path):
    assert main([sample_path, "--out", str(tmp_path)]) == 0
    return load_dataset(sample_path), load_timetable(str(tmp_path / "timetable.json"))


def test_tc_sys01_pipeline_produces_clash_free_timetable(generated):
    ds, entries = generated
    assert validate_timetable(entries, ds) == []


def test_tc_sys02_every_section_gets_required_hours(generated):
    ds, entries = generated
    got = defaultdict(int)
    for e in entries:
        got[(e.section_id, e.course_code)] += e.length
    for sec in ds.sections.values():
        for code in sec.course_codes:
            assert got[(sec.id, code)] == ds.courses[code].hours_per_week


def test_tc_sys03_no_double_booking_of_faculty_rooms_or_sections(generated):
    _, entries = generated
    for attr in ("faculty_id", "room_id", "section_id"):
        seen = set()
        for e in entries:
            for p in range(e.period, e.last_period + 1):
                key = (getattr(e, attr), e.day, p)
                assert key not in seen, f"double booking on {key}"
                seen.add(key)


def test_tc_sys04_faculty_availability_and_lunch_respected(generated):
    ds, entries = generated
    for e in entries:
        for p in range(e.period, e.last_period + 1):
            assert (e.day, p) not in ds.faculty[e.faculty_id].unavailable
        assert not (e.length == 2 and e.period == 3)


def test_tc_sys05_labs_use_lab_rooms_and_fit_strength(generated):
    ds, entries = generated
    for e in entries:
        room, course, sec = ds.rooms[e.room_id], ds.courses[e.course_code], ds.sections[e.section_id]
        assert room.is_lab == course.is_lab
        assert room.capacity >= sec.strength


def test_tc_sys06_rest_api_generate_then_validate(sample_path):
    client = create_app().test_client()
    with open(sample_path, encoding="utf-8") as fh:
        data = json.load(fh)
    tt = client.post("/api/generate", json=data).get_json()["timetable"]
    assert client.post("/api/validate", json={"dataset": data, "timetable": tt}).get_json()["violations"] == []


def test_tc_sys07_tampered_timetable_is_flagged(generated):
    ds, entries = generated
    clone = type(entries[0])(**{**entries[0].to_dict(), "section_id": "ECE-A"})
    assert validate_timetable(entries + [clone], ds)
