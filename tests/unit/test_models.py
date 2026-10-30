from ctgs.models import Dataset, Entry


def test_tc_m01_from_dict_builds_all_collections(tiny_ds):
    assert set(tiny_ds.faculty) == {"F1", "F2"}
    assert tiny_ds.faculty["F1"].unavailable == {("Mon", 1)}
    assert tiny_ds.rooms["L1"].is_lab and not tiny_ds.rooms["R1"].is_lab
    assert tiny_ds.courses["C2L"].is_lab
    assert tiny_ds.sections["S1"].course_codes == ["C1", "C2L"]


def test_tc_m02_valid_dataset_has_no_errors(tiny_ds):
    assert tiny_ds.validate() == []


def test_tc_m03_unknown_faculty(tiny_data):
    tiny_data["courses"][0]["faculty_id"] = "NOPE"
    assert any("unknown faculty" in e for e in Dataset.from_dict(tiny_data).validate())


def test_tc_m04_non_positive_hours(tiny_data):
    tiny_data["courses"][0]["hours_per_week"] = 0
    assert any("positive" in e for e in Dataset.from_dict(tiny_data).validate())


def test_tc_m05_odd_lab_hours(tiny_data):
    tiny_data["courses"][1]["hours_per_week"] = 3
    assert any("must be even" in e for e in Dataset.from_dict(tiny_data).validate())


def test_tc_m06_too_many_sessions_for_week(tiny_data):
    tiny_data["courses"][0]["hours_per_week"] = 6
    assert any("cannot fit" in e for e in Dataset.from_dict(tiny_data).validate())


def test_tc_m07_unknown_course_in_section(tiny_data):
    tiny_data["sections"][0]["courses"].append("GHOST")
    assert any("unknown course" in e for e in Dataset.from_dict(tiny_data).validate())


def test_tc_m08_no_room_big_enough(tiny_data):
    tiny_data["sections"][0]["strength"] = 500
    errors = Dataset.from_dict(tiny_data).validate()
    assert any("no classroom fits" in e for e in errors)
    assert any("no lab fits" in e for e in errors)


def test_tc_m09_section_exceeds_weekly_capacity(tiny_data):
    codes = [f"X{i}" for i in range(7)]          # 7 courses x 5h = 35h > 30 slots/week
    for c in codes:
        tiny_data["courses"].append({"code": c, "name": c, "hours_per_week": 5, "faculty_id": "F1"})
    tiny_data["sections"][1]["courses"] = codes
    assert any("weekly capacity" in e for e in Dataset.from_dict(tiny_data).validate())


def test_tc_m10_entry_overlap_logic():
    a = Entry("S", "C", "F", "R", "Mon", 1, 2)
    assert a.last_period == 2
    assert a.overlaps(Entry("S", "C", "F", "R", "Mon", 2))
    assert not a.overlaps(Entry("S", "C", "F", "R", "Mon", 3))
    assert not a.overlaps(Entry("S", "C", "F", "R", "Tue", 1))
    assert a.to_dict()["length"] == 2
