"""Hard-constraint checks used by the scheduler and the validator."""
from typing import List
from .models import DAYS, LUNCH_AFTER, PERIODS_PER_DAY, Dataset, Entry


def check_placement(entry: Entry, placed: List[Entry], ds: Dataset) -> List[str]:
    """Return violations if `entry` were added next to `placed` (empty = OK)."""
    if entry.day not in DAYS:
        return [f"Invalid day '{entry.day}'"]
    if entry.period < 1 or entry.last_period > PERIODS_PER_DAY:
        return [f"{entry.course_code}: outside periods 1-{PERIODS_PER_DAY}"]

    room = ds.rooms.get(entry.room_id)
    course = ds.courses.get(entry.course_code)
    section = ds.sections.get(entry.section_id)
    faculty = ds.faculty.get(entry.faculty_id)
    if None in (room, course, section, faculty):
        return [f"Unknown reference in entry {entry.section_id}/{entry.course_code}"]

    v: List[str] = []
    if entry.length > 1 and entry.period <= LUNCH_AFTER < entry.last_period:
        v.append(f"{entry.course_code}: block crosses the lunch break")
    if course.is_lab != room.is_lab:
        v.append(f"{entry.course_code}: room {room.id} is the wrong type")
    if room.capacity < section.strength:
        v.append(f"Room {room.id} too small for section {section.id}")
    if entry.faculty_id != course.faculty_id:
        v.append(f"{entry.course_code}: wrong faculty {entry.faculty_id}")
    for p in range(entry.period, entry.last_period + 1):
        if (entry.day, p) in faculty.unavailable:
            v.append(f"Faculty {faculty.id} unavailable on {entry.day} P{p}")

    for o in placed:
        if (o.section_id == entry.section_id and o.course_code == entry.course_code
                and o.day == entry.day):
            v.append(f"{entry.course_code} appears twice for {entry.section_id} on {entry.day}")
        if not entry.overlaps(o):
            continue
        if o.section_id == entry.section_id:
            v.append(f"Section clash: {entry.section_id} on {entry.day} P{entry.period}")
        if o.faculty_id == entry.faculty_id:
            v.append(f"Faculty clash: {entry.faculty_id} on {entry.day} P{entry.period}")
        if o.room_id == entry.room_id:
            v.append(f"Room clash: {entry.room_id} on {entry.day} P{entry.period}")
    return v


def validate_timetable(entries: List[Entry], ds: Dataset) -> List[str]:
    """Check a complete timetable: every placement plus required weekly hours."""
    violations: List[str] = []
    for i, e in enumerate(entries):
        violations += check_placement(e, entries[:i] + entries[i + 1:], ds)
    for sec in ds.sections.values():
        for code in sec.course_codes:
            need = ds.courses[code].hours_per_week
            got = sum(e.length for e in entries
                      if e.section_id == sec.id and e.course_code == code)
            if got != need:
                violations.append(f"Section {sec.id} {code}: scheduled {got}h, required {need}h")
    return list(dict.fromkeys(violations))
