import pytest
from ctgs.app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_tc_a01_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_tc_a02_home_page_renders_timetable(client):
    r = client.get("/")
    assert r.status_code == 200 and b"CSE-A" in r.data


def test_tc_a03_generate_ok(client, tiny_data):
    r = client.post("/api/generate", json=tiny_data)
    body = r.get_json()
    assert r.status_code == 200 and body["timetable"] and body["violations"] == []


def test_tc_a04_generate_rejects_non_object(client):
    assert client.post("/api/generate", json=[1, 2]).status_code == 400


def test_tc_a05_generate_rejects_malformed_dataset(client):
    assert client.post("/api/generate", json={"faculty": [{"name": "no id"}]}).status_code == 400


def test_tc_a06_generate_rejects_invalid_dataset(client, tiny_data):
    tiny_data["courses"][0]["faculty_id"] = "NOPE"
    r = client.post("/api/generate", json=tiny_data)
    assert r.status_code == 400 and r.get_json()["errors"]


def test_tc_a07_generate_unschedulable_422(client, tiny_data):
    from ctgs.models import DAYS
    tiny_data["faculty"][0]["unavailable"] = [[d, p] for d in DAYS for p in range(1, 7)]
    assert client.post("/api/generate", json=tiny_data).status_code == 422


def test_tc_a08_validate_ok_and_tampered(client, tiny_data):
    tt = client.post("/api/generate", json=tiny_data).get_json()["timetable"]
    r = client.post("/api/validate", json={"dataset": tiny_data, "timetable": tt})
    assert r.get_json()["violations"] == []
    r = client.post("/api/validate", json={"dataset": tiny_data, "timetable": tt + [tt[0]]})
    assert r.get_json()["violations"]


def test_tc_a09_validate_rejects_bad_payloads(client, tiny_data):
    assert client.post("/api/validate", json={"dataset": tiny_data}).status_code == 400
    assert client.post("/api/validate", json="oops").status_code == 400
    bad = dict(tiny_data)
    bad["courses"] = [dict(tiny_data["courses"][0], faculty_id="NOPE")]
    r = client.post("/api/validate", json={"dataset": bad, "timetable": []})
    assert r.status_code == 400
