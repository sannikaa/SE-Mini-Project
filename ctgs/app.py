"""Flask REST API: /health, /api/generate, /api/validate, and a demo page at /."""
from pathlib import Path
import secrets
from functools import wraps
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from .constraints import validate_timetable
from .io_utils import load_dataset, render_html
from .models import Dataset, Entry
from .scheduler import SchedulingError, generate
from . import auth

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_dataset.json"


def _parse_dataset(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    return Dataset.from_dict(payload)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=1800)

    def current_user():
        username = session.get("username")
        return next((u for u in auth.load_users() if u["username"] == username), None) if username else None

    def roles_required(*roles):
        def decorate(view):
            @wraps(view)
            def wrapped(*args, **kwargs):
                user = current_user()
                if user is None:
                    return jsonify(error="Sign in is required.", login=url_for("login")), 401
                if user["role"] not in roles:
                    return jsonify(error="Your role cannot perform this action."), 403
                if request.method == "POST" and request.headers.get("X-CSRF-Token") != session.get("csrf_token"):
                    return jsonify(error="Invalid or missing request token."), 400
                return view(*args, **kwargs)
            return wrapped
        return decorate

    @app.get("/login")
    def login():
        if current_user():
            return redirect(url_for("workspace"))
        return render_template("login.html", error=None)

    @app.post("/login")
    def login_post():
        user = auth.authenticate(request.form.get("username", ""), request.form.get("password", ""))
        if not user:
            return render_template("login.html", error="Username or password is incorrect."), 401
        session.clear()
        session.permanent = True
        session["username"] = user["username"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        return redirect(url_for("workspace"))

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/workspace")
    def workspace():
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        ds = load_dataset(str(SAMPLE))
        entries = auth.load_timetable()
        if entries is None:
            entries = generate(ds)
        status = auth.timetable_status()
        if user["role"] == "student":
            entries = [e for e in entries if e.section_id == user.get("section_id")] if status["status"] == "published" else []
        elif user["role"] == "faculty":
            entries = [e for e in entries if e.faculty_id == user.get("faculty_id")]
        return render_template("workspace.html", user=auth.public_user(user), roles=auth.ROLE_LABELS,
                               csrf_token=session["csrf_token"], sections=sorted(ds.sections),
                               faculty=sorted(ds.faculty.values(), key=lambda f: f.id), entries=entries,
                               status=status, unavailable=auth.load_preferences().get(user.get("faculty_id"), []))

    @app.get("/workspace/timetable")
    def workspace_timetable():
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        ds = load_dataset(str(SAMPLE))
        entries = auth.load_timetable() or generate(ds)
        if user["role"] == "student":
            entries = [e for e in entries if e.section_id == user.get("section_id")] if auth.timetable_status()["status"] == "published" else []
        elif user["role"] == "faculty":
            entries = [e for e in entries if e.faculty_id == user.get("faculty_id")]
        if user["role"] in ("student", "faculty"):
            # Restrict both the rows and the section tabs in the legacy timetable renderer.
            section_ids = {e.section_id for e in entries}
            course_ids = {e.course_code for e in entries}
            faculty_ids = {e.faculty_id for e in entries}
            room_ids = {e.room_id for e in entries}
            ds.sections = {key: value for key, value in ds.sections.items() if key in section_ids}
            ds.courses = {key: value for key, value in ds.courses.items() if key in course_ids}
            ds.faculty = {key: value for key, value in ds.faculty.items() if key in faculty_ids}
            ds.rooms = {key: value for key, value in ds.rooms.items() if key in room_ids}
        return render_html(entries, ds)

    @app.get("/workspace/api/users")
    @roles_required("admin")
    def workspace_users():
        return jsonify(users=auth.public_users())

    @app.post("/workspace/api/users")
    @roles_required("admin")
    def workspace_create_user():
        try:
            user = auth.create_user(request.get_json(silent=True), current_user()["username"])
        except (ValueError, TypeError) as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(user=user), 201

    @app.post("/workspace/api/generate")
    @roles_required("admin", "coordinator")
    def workspace_generate():
        ds = auth.apply_preferences(load_dataset(str(SAMPLE)))
        try:
            entries = generate(ds)
        except SchedulingError as exc:
            return jsonify(error=str(exc)), 422
        auth.save_timetable(entries)
        # A regenerated draft must be approved again.
        status_path = auth.DATA_DIR / "timetable_status.json"
        if status_path.exists():
            status_path.unlink()
        return jsonify(count=len(entries), status="draft")

    @app.post("/workspace/api/approve")
    @roles_required("admin", "hod")
    def workspace_approve():
        if auth.load_timetable() is None:
            return jsonify(error="Generate and save a timetable draft before approving it."), 400
        state = auth.approve_timetable(current_user()["username"])
        return jsonify(status=state)

    @app.post("/workspace/api/availability")
    @roles_required("faculty")
    def workspace_availability():
        body = request.get_json(silent=True) or {}
        try:
            slots = auth.save_availability(current_user()["faculty_id"], body.get("day", ""),
                                           int(body.get("period", 0)), bool(body.get("unavailable")))
        except (ValueError, TypeError) as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(unavailable=slots, note="Saved. The coordinator will use this preference on the next generation.")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/")
    def home():
        ds = load_dataset(str(SAMPLE))
        page = render_html(generate(ds), ds)
        return page.replace('<div class="avatar">CT</div>', '<a href="/login" style="color:#237451;text-decoration:none;font-weight:650">Role workspace&nbsp; ↗</a>')

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
