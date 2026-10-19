from datetime import date, timedelta

import pytest

from app import main


@pytest.fixture
def client():
    main.ITEMS.clear()
    main._next_id = 1
    return main.app.test_client()


def iso(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def test_status_thresholds():
    assert main.status_for(-1) == "expired"
    assert main.status_for(0) == "use_soon"
    assert main.status_for(3) == "use_soon"
    assert main.status_for(4) == "fresh"


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_add_and_list_sorted(client):
    client.post("/items", json={"name": "rice", "expires": iso(90)})
    client.post("/items", json={"name": "milk", "expires": iso(2)})
    data = client.get("/items").get_json()
    assert [i["name"] for i in data] == ["milk", "rice"]
    assert data[0]["status"] == "use_soon"


def test_validation(client):
    assert client.post("/items", json={"name": "x"}).status_code == 400
    assert client.post("/items", json={"name": "x", "expires": "tomorrow"}).status_code == 400


def test_expiring_window(client):
    client.post("/items", json={"name": "yogurt", "expires": iso(1)})
    client.post("/items", json={"name": "honey", "expires": iso(500)})
    names = [i["name"] for i in client.get("/items/expiring?days=7").get_json()]
    assert names == ["yogurt"]
