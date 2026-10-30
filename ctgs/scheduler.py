"""Backtracking timetable generator."""
from collections import Counter
from typing import Iterator, List, Tuple
from .constraints import check_placement
from .models import DAYS, PERIODS_PER_DAY, Dataset, Entry


class InvalidDatasetError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


class SchedulingError(Exception):
    pass


def build_sessions(ds: Dataset) -> List[Tuple[str, str, int]]:
    """Expand each section's courses into (section, course, length) sessions."""
    sessions = []
    for sec in ds.sections.values():
        for code in sec.course_codes:
            c = ds.courses[code]
            if c.is_lab:
                sessions += [(sec.id, code, 2)] * (c.hours_per_week // 2)
            else:
                sessions += [(sec.id, code, 1)] * c.hours_per_week
    sessions.sort(key=lambda s: (-s[2], s[0], s[1]))  # hardest (labs) first
    return sessions


def _candidates(sec_id: str, code: str, length: int,
                placed: List[Entry], ds: Dataset) -> Iterator[Entry]:
    sec, course = ds.sections[sec_id], ds.courses[code]
    load = Counter()
    for e in placed:
        if e.section_id == sec_id:
            load[e.day] += e.length
    days = sorted(DAYS, key=lambda d: load[d])  # spread load across the week
    rooms = sorted((r for r in ds.rooms.values()
                    if r.is_lab == course.is_lab and r.capacity >= sec.strength),
                   key=lambda r: r.capacity)
    for day in days:
        for start in range(1, PERIODS_PER_DAY - length + 2):
            for room in rooms:
                cand = Entry(sec_id, code, course.faculty_id, room.id, day, start, length)
                if not check_placement(cand, placed, ds):
                    yield cand


def generate(ds: Dataset, max_steps: int = 50000) -> List[Entry]:
    errors = ds.validate()
    if errors:
        raise InvalidDatasetError(errors)
    sessions = build_sessions(ds)
    placed: List[Entry] = []
    steps = 0

    def backtrack(i: int) -> bool:
        nonlocal steps
        if i == len(sessions):
            return True
        steps += 1
        if steps > max_steps:
            raise SchedulingError("Step limit reached before a timetable was found")
        sec_id, code, length = sessions[i]
        for cand in _candidates(sec_id, code, length, placed, ds):
            placed.append(cand)
            if backtrack(i + 1):
                return True
            placed.pop()
        return False

    if not backtrack(0):
        raise SchedulingError("No feasible timetable exists for the given constraints")
    return placed
