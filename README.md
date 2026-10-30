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
