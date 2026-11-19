# College Timetable Generation System (CTGS)

Generates a clash-free weekly timetable for college sections from faculty, room, course and section data.

**Hard constraints enforced:** no section / faculty / room double-booking, room capacity, lab courses only in lab rooms
(2-period blocks that never cross lunch), faculty unavailability, max one session of a course per section per day.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python -m ctgs.cli data/sample_dataset.json --out out   # writes timetable.json / .csv / .html
python -m ctgs.app                                       # web demo at http://127.0.0.1:5000
```
REST API: `GET /health`, `POST /api/generate` (dataset JSON), `POST /api/validate` (`{dataset, timetable}`).

## Test + generate all Part-3 reports
```bash
bash scripts/run_tests.sh        # on Windows use Git Bash or WSL
```
Outputs in `docs/reports/`: unit test report, system validation report, code coverage, branch coverage.

## Layout
`ctgs/` source (models, constraints, scheduler, io_utils, cli, app) - `tests/unit`, `tests/system` - `data/` sample input - `docs/` SRS, SAD, Test Plan, reports.

## Role-based web workspace (local prototype)
Open `http://127.0.0.1:5000/login` after starting the Flask app to use the five CTGS roles:

- **Administrator** (`admin`): creates user accounts and can generate or publish schedules.
- **Timetable Coordinator** (`coordinator`): generates a draft schedule using faculty availability preferences.
- **Department Head** (`hod`): reviews and publishes a saved draft.
- **Faculty** (`faculty`): sees only their assigned sessions and can save unavailable day/period slots.
- **Student** (`student`): sees only their assigned section, and only after a schedule is published.

For local walkthroughs, each starter account uses `CTGSdemo2026!`. The app creates hashed accounts in `data/users.json` on first use. Administrator-created users need a password of at least 12 characters. Faculty accounts must be linked to an existing faculty ID; student accounts must be linked to an existing section ID. Local accounts, preferences and schedule approval state are git-ignored and stored in `data/users.json`, `data/user_preferences.json`, `data/current_timetable.json` and `data/timetable_status.json`.

This is a coursework prototype: the starter accounts and the legacy demonstration/API routes are intended for local development, not public deployment. Replace the starter credentials and add deployment-grade secret management and API authorization before hosting it publicly.
