import json
from ctgs.cli import main


def test_tc_u01_success_writes_outputs(sample_path, tmp_path):
    assert main([sample_path, "--out", str(tmp_path)]) == 0
    for name in ("timetable.json", "timetable.csv", "timetable.html"):
        assert (tmp_path / name).exists()


def test_tc_u02_missing_file_returns_2(tmp_path):
    assert main([str(tmp_path / "nope.json")]) == 2


def test_tc_u03_bad_json_returns_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert main([str(bad)]) == 2


def test_tc_u04_invalid_dataset_returns_1(tiny_data, tmp_path):
    tiny_data["courses"][0]["faculty_id"] = "NOPE"
    p = tmp_path / "d.json"
    p.write_text(json.dumps(tiny_data))
    assert main([str(p), "--out", str(tmp_path)]) == 1


def test_tc_u05_infeasible_returns_3(tiny_data, tmp_path):
    from ctgs.models import DAYS
    tiny_data["faculty"][0]["unavailable"] = [[d, p] for d in DAYS for p in range(1, 7)]
    p = tmp_path / "d.json"
    p.write_text(json.dumps(tiny_data))
    assert main([str(p), "--out", str(tmp_path)]) == 3
