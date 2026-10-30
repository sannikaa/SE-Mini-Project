"""Flask REST API: /health, /api/generate, /api/validate, and a demo page at /."""
from pathlib import Path
from flask import Flask, jsonify, request
from .constraints import validate_timetable
from .io_utils import load_dataset, render_html
from .models import Dataset, Entry
from .scheduler import SchedulingError, generate

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_dataset.json"


def _parse_dataset(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    return Dataset.from_dict(payload)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/")
    def home():
        ds = load_dataset(str(SAMPLE))
        return render_html(generate(ds), ds)

    @app.post("/api/generate")
    def api_generate():
        try:
            ds = _parse_dataset(request.get_json(silent=True))
        except (ValueError, KeyError, TypeError) as exc:
            return jsonify(errors=[f"Malformed dataset: {exc}"]), 400
        errors = ds.validate()
        if errors:
            return jsonify(errors=errors), 400
        try:
            entries = generate(ds)
        except SchedulingError as exc:
            return jsonify(errors=[str(exc)]), 422
        return jsonify(timetable=[e.to_dict() for e in entries],
                       violations=validate_timetable(entries, ds))

    @app.post("/api/validate")
    def api_validate():
        body = request.get_json(silent=True)
        try:
            ds = _parse_dataset((body or {}).get("dataset") if isinstance(body, dict) else None)
            entries = [Entry(**e) for e in body["timetable"]]
        except (ValueError, KeyError, TypeError) as exc:
            return jsonify(errors=[f"Malformed request: {exc}"]), 400
        errors = ds.validate()
        if errors:
            return jsonify(errors=errors), 400
        return jsonify(violations=validate_timetable(entries, ds))

    return app


if __name__ == "__main__":  # pragma: no cover
    create_app().run(debug=True)
