from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_login():
    res = client.post("/auth/login", json={"username": "instructor1", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["username"] == "instructor1"


def test_get_trainees_and_groups():
    res1 = client.get("/trainees/")
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)

    res2 = client.get("/groups/")
    assert res2.status_code == 200
    assert isinstance(res2.json(), list)


def test_get_weapons_and_targets():
    res1 = client.get("/weapons")
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)

    res2 = client.get("/targets")
    assert res2.status_code == 200
    assert isinstance(res2.json(), list)


def test_get_calibration():
    res = client.get("/calibration/screen")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
