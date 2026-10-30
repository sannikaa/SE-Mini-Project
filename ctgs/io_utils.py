"""Loading datasets and exporting timetables (JSON / CSV / HTML)."""
import csv
import html
import json
from typing import Dict, List
from .models import DAYS, PERIODS_PER_DAY, Dataset, Entry


def load_dataset(path: str) -> Dataset:
    with open(path, encoding="utf-8") as fh:
        return Dataset.from_dict(json.load(fh))


def save_json(entries: List[Entry], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([e.to_dict() for e in entries], fh, indent=2)


def load_timetable(path: str) -> List[Entry]:
    with open(path, encoding="utf-8") as fh:
        return [Entry(**d) for d in json.load(fh)]


def save_csv(entries: List[Entry], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["section", "course", "faculty", "room", "day", "start_period", "length"])
        for e in entries:
            w.writerow([e.section_id, e.course_code, e.faculty_id, e.room_id,
                        e.day, e.period, e.length])


def section_grid(entries: List[Entry], section_id: str) -> Dict[str, List[str]]:
    grid = {d: ["-"] * PERIODS_PER_DAY for d in DAYS}
    for e in entries:
        if e.section_id == section_id:
            for p in range(e.period, e.last_period + 1):
                grid[e.day][p - 1] = e.course_code
    return grid


def render_html(entries: List[Entry], ds: Dataset) -> str:
    out = ["<!doctype html><html><head><meta charset='utf-8'><title>CTGS Timetable</title>",
           "<style>body{font-family:sans-serif}table{border-collapse:collapse;margin:1em 0}"
           "td,th{border:1px solid #888;padding:6px 10px;text-align:center}</style>",
           "</head><body><h1>College Timetable</h1>"]
    for sec_id in ds.sections:
        grid = section_grid(entries, sec_id)
        out.append(f"<h2>Section {html.escape(sec_id)}</h2><table><tr><th>Day</th>")
        out += [f"<th>P{p}</th>" for p in range(1, PERIODS_PER_DAY + 1)]
        out.append("</tr>")
        for day in DAYS:
            cells = "".join(f"<td>{html.escape(c)}</td>" for c in grid[day])
            out.append(f"<tr><th>{day}</th>{cells}</tr>")
        out.append("</table>")
    out.append("</body></html>")
    return "".join(out)
