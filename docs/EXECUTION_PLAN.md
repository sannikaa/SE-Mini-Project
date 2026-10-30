# CTGS - Execution Plan (30 Oct - 6 Nov)

## A. One-time GitHub setup (Member 4 drives, everyone does it once)
1. Repo `SE-Mini-Project` -> Settings -> Collaborators: add all 4 members.
2. Locally: `git clone https://github.com/sannikaa/SE-Mini-Project && cd SE-Mini-Project`
3. Tidy existing docs: `mkdir docs && git mv "CTGS_SRS (1).docx" docs/CTGS_SRS.docx` (same for SAD and Test_Plan).
4. Copy this project's files in (keep `docs/`), then:
   `git add . && git commit -m "chore: add CTGS code, tests, CI" && git push origin main`
5. Create `develop`: `git checkout -b develop && git push -u origin develop`.
6. Settings -> Branches -> protect `main`: require a pull request + 1 approval + passing CI check.
7. Check the Actions tab: the CI run should be green.

## B. Daily git workflow (everyone)
```bash
git checkout develop && git pull
git checkout -b feature/<name>-<task>        # e.g. feature/m3-scheduler-tuning
# ...work, then
git add <files> && git commit -m "feat(scheduler): prefer even spread across days"
git push -u origin feature/<name>-<task>
```
Open a PR into `develop`, a teammate reviews, squash-merge. Commit prefixes: `feat`, `fix`, `test`, `docs`, `chore`.
Merge `develop` -> `main` only on 5 Nov after all tests pass; tag it `git tag v1.0 && git push --tags`.

## C. Work division
| Member | Owns (code) | Owns (tests) | Owns (docs) |
|---|---|---|---|
| M1 - Data & I/O | `models.py`, `io_utils.py`, `data/` | `test_models.py`, `test_io_utils.py` | Update SRS/SAD wherever sprints changed them; README |
| M2 - Constraints | `constraints.py` | `test_constraints.py` | **Test Case Document update** (map every `TC-xx` id to its requirement) |
| M3 - Scheduler | `scheduler.py` (+ Sprint-3 spillover: soft constraints such as no gaps / faculty daily load) | `test_scheduler.py` | Unit Test Report review + analysis section |
| M4 - Interfaces & QA | `cli.py`, `app.py`, `.github/`, `scripts/` | `test_cli.py`, `test_api.py`, `tests/system/` | System Validation Report, coverage reports, final upload to `docs/reports/` |

Rule: whoever owns a module fixes failing tests for it. Test ids (`TC-M`, `TC-C`, `TC-S`, `TC-I`, `TC-U`, `TC-A`, `TC-SYS`) are in the test function names.

## D. Timeline
| Date | What |
|---|---|
| Fri 30 Oct - Sun 1 Nov | Do section A. Everyone reads the SRS and lists requirements this code does not yet cover (= spillover). Decide: is Sprint-3 needed? If yes, M3 + M1 build it Mon-Wed on `feature/` branches, with tests alongside. |
| Mon 2 Nov | Run `bash scripts/run_tests.sh` locally (all green). M2 updates the Test Case Document to match what changed in the sprints. Add/adjust tests for any changed behaviour. |
| Tue 3 Nov | Testing per the Test Plan: unit tests per owner, fix defects via PRs. Log each defect (what, where, fix) for the report. |
| Wed 4 Nov | System testing against SRS requirements (`tests/system`, plus manual run of the web demo and API). Add a requirement-to-test traceability table to the System Validation Report. |
| Thu 5 Nov | Freeze code. Merge `develop` -> `main`. Run `scripts/run_tests.sh` on `main`; confirm coverage targets (aim >=90% line, >=85% branch). |
| Fri 6 Nov | Commit `docs/reports/` (unit, system validation, code coverage, branch coverage) plus the updated Test Case Document; push; tag `v1.0`; final check that the repo opens cleanly for the evaluator. |

## E. Report checklist (all produced by `scripts/run_tests.sh`)
- Unit Test Report -> `docs/reports/unit_test_report.html`
- System Validation Report -> `docs/reports/system_validation_report.html` (+ your traceability table)
- Code Coverage Report -> `docs/reports/code_coverage_report.txt` and `code_coverage_html/`
- Branch Coverage Report -> `docs/reports/branch_coverage_report.txt` and `branch_coverage_html/`
