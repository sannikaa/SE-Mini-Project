"""Local demo accounts and role helpers for the CTGS web workspace."""
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from .io_utils import load_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
USERS_FILE = DATA_DIR / "users.json"
PREFERENCES_FILE = DATA_DIR / "user_preferences.json"
ROLE_LABELS = {
    "admin": "Administrator",
    "coordinator": "Timetable Coordinator",
    "hod": "Department Head (HoD)",
    "faculty": "Faculty",
    "student": "Student",
}
DEMO_PASSWORD = "CTGSdemo2026!"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def ensure_demo_users() -> None:
    """Create local demo accounts once; the resulting file is git-ignored."""
    if USERS_FILE.exists():
        return
    ds = load_dataset(str(PROJECT_ROOT / "data" / "sample_dataset.json"))
    demos = [
        {"username": "admin", "display_name": "CTGS Administrator", "role": "admin"},
        {"username": "coordinator", "display_name": "Timetable Coordinator", "role": "coordinator"},
        {"username": "hod", "display_name": "Department Head", "role": "hod"},
        {"username": "faculty", "display_name": ds.faculty["F1"].name, "role": "faculty", "faculty_id": "F1"},
        {"username": "student", "display_name": "CSE-A Student", "role": "student", "section_id": "CSE-A"},
    ]
    for item in demos:
        item["password_hash"] = generate_password_hash(DEMO_PASSWORD, method="scrypt")
        item["created_by"] = "system"
    _write_json(USERS_FILE, demos)


def load_users() -> List[dict]:
    ensure_demo_users()
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def save_users(users: List[dict]) -> None:
    _write_json(USERS_FILE, users)


def authenticate(username: str, password: str) -> Optional[dict]:
    username = username.strip().lower()
    for user in load_users():
        if user["username"] == username and check_password_hash(user["password_hash"], password):
            return user
    return None


def public_user(user: dict) -> dict:
    return {key: user[key] for key in ("username", "display_name", "role", "faculty_id", "section_id") if key in user}


def public_users() -> List[dict]:
    return [public_user(user) for user in load_users()]


def create_user(payload: dict, created_by: str) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("User details must be a JSON object.")
    username = str(payload.get("username", "")).strip().lower()
    display_name = str(payload.get("display_name", "")).strip()
    role = str(payload.get("role", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not re.fullmatch(r"[a-z0-9._-]{3,32}", username):
        raise ValueError("Username must be 3–32 characters: letters, numbers, dots, underscores or hyphens.")
    if not display_name:
        raise ValueError("Display name is required.")
    if role not in ROLE_LABELS:
        raise ValueError("Choose one of the five CTGS roles.")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters.")
    users = load_users()
    if any(user["username"] == username for user in users):
        raise ValueError("That username already exists.")

    ds = load_dataset(str(PROJECT_ROOT / "data" / "sample_dataset.json"))
    user = {
        "username": username,
        "display_name": display_name,
        "role": role,
        "password_hash": generate_password_hash(password, method="scrypt"),
        "created_by": created_by,
    }
    if role == "faculty":
        faculty_id = str(payload.get("faculty_id", ""))
        if faculty_id not in ds.faculty:
            raise ValueError("Choose a faculty ID from the current dataset.")
        user["faculty_id"] = faculty_id
    if role == "student":
        section_id = str(payload.get("section_id", ""))
        if section_id not in ds.sections:
            raise ValueError("Choose a section from the current dataset.")
        user["section_id"] = section_id
    users.append(user)
    save_users(users)
    return public_user(user)


def load_preferences() -> Dict[str, List[List[object]]]:
    if not PREFERENCES_FILE.exists():
        return {}
    return json.loads(PREFERENCES_FILE.read_text(encoding="utf-8"))


def save_availability(faculty_id: str, day: str, period: int, unavailable: bool) -> List[List[object]]:
    from .models import DAYS, PERIODS_PER_DAY

    if day not in DAYS:
        raise ValueError("Choose a working day from Monday to Friday.")
    if period < 1 or period > PERIODS_PER_DAY:
        raise ValueError(f"Period must be between 1 and {PERIODS_PER_DAY}.")
    preferences = load_preferences()
    blocked = {(str(d), int(p)) for d, p in preferences.get(faculty_id, [])}
    slot = (day, period)
    if unavailable:
        blocked.add(slot)
    else:
        blocked.discard(slot)
    preferences[faculty_id] = [[d, p] for d, p in sorted(blocked)]
    _write_json(PREFERENCES_FILE, preferences)
    return preferences[faculty_id]


def apply_preferences(dataset):
    """Merge faculty-entered unavailable periods into the in-memory dataset."""
    for faculty_id, slots in load_preferences().items():
        if faculty_id in dataset.faculty:
            dataset.faculty[faculty_id].unavailable.update((str(day), int(period)) for day, period in slots)
    return dataset


def save_timetable(entries) -> None:
    _write_json(DATA_DIR / "current_timetable.json", [entry.to_dict() for entry in entries])


def load_timetable():
    path = DATA_DIR / "current_timetable.json"
    if not path.exists():
        return None
    from .models import Entry
    return [Entry(**item) for item in json.loads(path.read_text(encoding="utf-8"))]


def approve_timetable(approved_by: str) -> dict:
    path = DATA_DIR / "timetable_status.json"
    state = {
        "status": "published",
        "approved_by": approved_by,
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(path, state)
    return state


def timetable_status() -> dict:
    path = DATA_DIR / "timetable_status.json"
    if not path.exists():
        return {"status": "draft", "approved_by": None, "approved_at": None}
    return json.loads(path.read_text(encoding="utf-8"))
