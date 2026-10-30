"""Command line interface: python -m ctgs.cli data/sample_dataset.json --out out"""
import argparse
import os
from .io_utils import load_dataset, render_html, save_csv, save_json
from .scheduler import SchedulingError, generate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CTGS timetable generator")
    parser.add_argument("dataset", help="path to dataset JSON")
    parser.add_argument("--out", default="out", help="output directory")
    args = parser.parse_args(argv)

    try:
        ds = load_dataset(args.dataset)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Could not read dataset: {exc}")
        return 2
    errors = ds.validate()
    if errors:
        print("Invalid dataset:\n  " + "\n  ".join(errors))
        return 1
    try:
        entries = generate(ds)
    except SchedulingError as exc:
        print(f"Scheduling failed: {exc}")
        return 3

    os.makedirs(args.out, exist_ok=True)
    save_json(entries, os.path.join(args.out, "timetable.json"))
    save_csv(entries, os.path.join(args.out, "timetable.csv"))
    with open(os.path.join(args.out, "timetable.html"), "w", encoding="utf-8") as fh:
        fh.write(render_html(entries, ds))
    print(f"Timetable written to {args.out}/ ({len(entries)} sessions)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
