from ctgs.constraints import check_placement, validate_timetable
from ctgs.models import Entry


def ok_entry(**kw):
    base = dict(section_id="S1", course_code="C1", faculty_id="F1",
                room_id="R1", day="Tue", period=1, length=1)
    base.update(kw)
    return Entry(**base)


def has(violations, text):
    return any(text in v for v in violations)


def test_tc_c01_valid_placement(tiny_ds):
    assert check_placement(ok_entry(), [], tiny_ds) == []


def test_tc_c02_invalid_day(tiny_ds):
    assert has(check_placement(ok_entry(day="Sun"), [], tiny_ds), "Invalid day")


def test_tc_c03_outside_hours(tiny_ds):
    assert has(check_placement(ok_entry(period=0), [], tiny_ds), "outside periods")
    assert has(check_placement(ok_entry(period=6, length=2), [], tiny_ds), "outside periods")


def test_tc_c04_unknown_reference(tiny_ds):
    assert has(check_placement(ok_entry(room_id="X"), [], tiny_ds), "Unknown reference")


def test_tc_c05_lunch_break_crossing(tiny_ds):
    lab = ok_entry(course_code="C2L", faculty_id="F2", room_id="L1", period=3, length=2)
    assert has(check_placement(lab, [], tiny_ds), "lunch")


def test_tc_c06_lab_before_lunch_is_fine(tiny_ds):
    lab = ok_entry(course_code="C2L", faculty_id="F2", room_id="L1", period=1, length=2)
    assert check_placement(lab, [], tiny_ds) == []


def test_tc_c07_room_type_mismatch(tiny_ds):
    assert has(check_placement(ok_entry(room_id="L1"), [], tiny_ds), "wrong type")


def test_tc_c08_room_capacity(tiny_ds):
    tiny_ds.rooms["R1"].capacity = 10
    assert has(check_placement(ok_entry(), [], tiny_ds), "too small")


def test_tc_c09_wrong_faculty(tiny_ds):
    assert has(check_placement(ok_entry(faculty_id="F2"), [], tiny_ds), "wrong faculty")


def test_tc_c10_faculty_unavailable(tiny_ds):
    assert has(check_placement(ok_entry(day="Mon", period=1), [], tiny_ds), "unavailable")


def test_tc_c11_faculty_and_room_clash(tiny_ds):
    other = ok_entry(section_id="S2")
    v = check_placement(ok_entry(), [other], tiny_ds)
    assert has(v, "Faculty clash") and has(v, "Room clash")


def test_tc_c12_section_clash(tiny_ds):
    lab = ok_entry(course_code="C2L", faculty_id="F2", room_id="L1", period=1, length=2)
    assert has(check_placement(ok_entry(), [lab], tiny_ds), "Section clash")


def test_tc_c13_same_course_twice_in_a_day(tiny_ds):
    v = check_placement(ok_entry(period=5), [ok_entry()], tiny_ds)
    assert has(v, "twice")


def test_tc_c14_non_overlapping_entries_are_fine(tiny_ds):
    other = ok_entry(section_id="S2", day="Wed")
    assert check_placement(ok_entry(), [other], tiny_ds) == []


def test_tc_c15_validate_timetable_detects_missing_hours(tiny_ds):
    v = validate_timetable([ok_entry()], tiny_ds)
    assert has(v, "scheduled 1h, required 3h")


def test_tc_c16_validate_timetable_detects_clash(tiny_ds):
    v = validate_timetable([ok_entry(), ok_entry(section_id="S2")], tiny_ds)
    assert has(v, "Faculty clash")
