#!/usr/bin/env bash
# Generates every report required by Mini-Project Part 3 into docs/reports/
set -euo pipefail
OUT=docs/reports
rm -rf "$OUT" && mkdir -p "$OUT"

echo ">> 1/3 Unit tests + code (line) coverage"
COVERAGE_FILE=.coverage.line pytest tests/unit \
  --html="$OUT/unit_test_report.html" --self-contained-html \
  --junitxml="$OUT/unit_test_junit.xml" \
  --cov=ctgs --cov-report="html:$OUT/code_coverage_html"
COVERAGE_FILE=.coverage.line coverage report -m > "$OUT/code_coverage_report.txt"

echo ">> 2/3 Branch coverage"
COVERAGE_FILE=.coverage.branch pytest tests/unit \
  --cov=ctgs --cov-branch --cov-report="html:$OUT/branch_coverage_html"
COVERAGE_FILE=.coverage.branch coverage report -m > "$OUT/branch_coverage_report.txt"

echo ">> 3/3 System validation"
pytest tests/system \
  --html="$OUT/system_validation_report.html" --self-contained-html \
  --junitxml="$OUT/system_validation_junit.xml"

# coverage writes a '*' .gitignore into its html folders; remove so reports can be committed
find "$OUT" -name .gitignore -delete
echo "Reports written to $OUT/"
