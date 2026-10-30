import csv
from ctgs.io_utils import (load_dataset, load_timetable, render_html,
                           save_csv, save_json, section_grid)
from ctgs.models import Entry


def _entries():
    return [Entry("S1", "C1", "F1", "R1", "Tue", 1),
            Entry("S1", "C2L", "F2", "L1", "Wed", 1, 2)]


def test_tc_i01_load_dataset(sample_path):
    ds = load_dataset(sample_path)
    assert "CSE-A" in ds.sections and len(ds.rooms) == 5


def test_tc_i02_json_roundtrip(tmp_path):
    p = tmp_path / "t.json"
    save_json(_entries(), str(p))
    assert load_timetable(str(p)) == _entries()


def test_tc_i03_csv_export(tmp_path):
    p = tmp_path / "t.csv"
    save_csv(_entries(), str(p))
    rows = list(csv.reader(open(p, encoding="utf-8")))
    assert rows[0][0] == "section" and len(rows) == 3


def test_tc_i04_section_grid_marks_all_periods():
    grid = section_grid(_entries(), "S1")
    assert grid["Tue"][0] == "C1" and grid["Wed"][:2] == ["C2L", "C2L"]
    assert grid["Mon"] == ["-"] * 6


def test_tc_i05_render_html_contains_sections(tiny_ds):
    page = render_html(_entries(), tiny_ds)
    assert "Section S1" in page and "Section S2" in page and "C2L" in page
