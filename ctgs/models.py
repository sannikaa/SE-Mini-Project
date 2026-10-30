"""Domain models and input validation for CTGS."""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Tuple

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
PERIODS_PER_DAY = 6
LUNCH_AFTER = 3  # lunch break sits between period 3 and period 4


@dataclass
class Faculty:
    id: str
    name: str
    unavailable: Set[Tuple[str, int]] = field(default_factory=set)


@dataclass
class Room:
    id: str
    capacity: int
    is_lab: bool = False


@dataclass
class Course:
    code: str
    name: str
    hours_per_week: int
    faculty_id: str
    is_lab: bool = False  # labs are scheduled as 2-period blocks


@dataclass
class Section:
    id: str
    strength: int
    course_codes: List[str]


@dataclass
class Entry:
    """One scheduled session (1 period for theory, 2 consecutive for labs)."""
    section_id: str
    course_code: str
    faculty_id: str
    room_id: str
    day: str
    period: int
    length: int = 1

    @property
    def last_period(self) -> int:
        return self.period + self.length - 1

    def overlaps(self, other: "Entry") -> bool:
        return (self.day == other.day
                and self.period <= other.last_period
                and other.period <= self.last_period)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Dataset:
    faculty: Dict[str, Faculty] = field(default_factory=dict)
    rooms: Dict[str, Room] = field(default_factory=dict)
    courses: Dict[str, Course] = field(default_factory=dict)
    sections: Dict[str, Section] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Dataset":
        ds = cls()
        for f in data.get("faculty", []):
            blocked = {(d, int(p)) for d, p in f.get("unavailable", [])}
            ds.faculty[f["id"]] = Faculty(f["id"], f["name"], blocked)
        for r in data.get("rooms", []):
            ds.rooms[r["id"]] = Room(r["id"], r["capacity"], r.get("is_lab", False))
        for c in data.get("courses", []):
            ds.courses[c["code"]] = Course(c["code"], c["name"], c["hours_per_week"],
                                           c["faculty_id"], c.get("is_lab", False))
        for s in data.get("sections", []):
            ds.sections[s["id"]] = Section(s["id"], s["strength"], list(s["courses"]))
        return ds

    def validate(self) -> List[str]:
        """Return a list of human-readable input errors (empty list = valid)."""
        errors: List[str] = []
        for c in self.courses.values():
            if c.faculty_id not in self.faculty:
                errors.append(f"Course {c.code}: unknown faculty {c.faculty_id}")
            if c.hours_per_week <= 0:
                errors.append(f"Course {c.code}: hours_per_week must be positive")
            if c.is_lab and c.hours_per_week % 2:
                errors.append(f"Lab course {c.code}: hours_per_week must be even")
            sessions = c.hours_per_week // 2 if c.is_lab else c.hours_per_week
            if sessions > len(DAYS):
                errors.append(f"Course {c.code}: {sessions} sessions cannot fit "
                              f"in {len(DAYS)} days (max one session per day)")
        max_theory = max((r.capacity for r in self.rooms.values() if not r.is_lab), default=0)
        max_lab = max((r.capacity for r in self.rooms.values() if r.is_lab), default=0)
        for s in self.sections.values():
            total = 0
            for code in s.course_codes:
                if code not in self.courses:
                    errors.append(f"Section {s.id}: unknown course {code}")
                    continue
                course = self.courses[code]
                total += course.hours_per_week
                cap = max_lab if course.is_lab else max_theory
                if cap < s.strength:
                    kind = "lab" if course.is_lab else "classroom"
                    errors.append(f"Section {s.id}: no {kind} fits strength {s.strength}")
            if total > len(DAYS) * PERIODS_PER_DAY:
                errors.append(f"Section {s.id}: {total}h exceeds weekly capacity")
        return list(dict.fromkeys(errors))
