import copy
import pytest
import requests
import app as app_module
from app import app

ORIGINAL = copy.deepcopy(app_module.inventory)


class FakeResponse:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("error")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app_module.inventory[:] = copy.deepcopy(ORIGINAL)
    app_module.next_id = 3
    with app.test_client() as c:
        yield c


# ---- CRUD ----
def test_get_all(client):
    r = client.get("/inventory")
    assert r.status_code == 200 and len(r.get_json()) == 2


def test_get_one(client):
    assert client.get("/inventory/1").get_json()["product_name"] == "Almond Milk"


def test_get_one_not_found(client):
    assert client.get("/inventory/999").status_code == 404


def test_create(client):
    r = client.post("/inventory", json={"product_name": "Oats", "price": 2.5, "stock": 10})
    assert r.status_code == 201
    assert r.get_json()["id"] == 3
    assert len(client.get("/inventory").get_json()) == 3


def test_create_missing_name(client):
    assert client.post("/inventory", json={"price": 1}).status_code == 400


def test_update(client):
    r = client.patch("/inventory/1", json={"price": 5.25, "stock": 7})
    assert r.status_code == 200
    assert r.get_json()["price"] == 5.25 and r.get_json()["stock"] == 7


def test_update_not_found(client):
    assert client.patch("/inventory/999", json={"stock": 1}).status_code == 404


def test_delete(client):
    assert client.delete("/inventory/1").status_code == 200
    assert client.get("/inventory/1").status_code == 404


def test_delete_not_found(client):
    assert client.delete("/inventory/999").status_code == 404


# ---- External API (mocked) ----
def test_external_barcode(client, monkeypatch):
    monkeypatch.setattr(app_module.requests, "get", lambda *a, **k: FakeResponse(
        {"status": 1, "product": {"code": "123", "product_name": "Nutella", "brands": "Ferrero",
                                   "ingredients_text": "Sugar, palm oil"}}))
    r = client.get("/external/barcode/123")
    assert r.status_code == 200 and r.get_json()["product_name"] == "Nutella"


def test_external_barcode_not_found(client, monkeypatch):
    monkeypatch.setattr(app_module.requests, "get", lambda *a, **k: FakeResponse({"status": 0}))
    assert client.get("/external/barcode/000").status_code == 404


def test_external_search(client, monkeypatch):
    monkeypatch.setattr(app_module.requests, "get", lambda *a, **k: FakeResponse(
        {"products": [{"code": "1", "product_name": "Cola", "brands": "X"}]}))
    r = client.get("/external/search?name=cola")
    assert r.status_code == 200 and r.get_json()[0]["product_name"] == "Cola"


def test_external_search_requires_name(client):
    assert client.get("/external/search").status_code == 400


def test_import_by_barcode(client, monkeypatch):
    monkeypatch.setattr(app_module.requests, "get", lambda *a, **k: FakeResponse(
        {"status": 1, "product": {"code": "123", "product_name": "Nutella", "brands": "Ferrero"}}))
    r = client.post("/inventory/import", json={"barcode": "123", "price": 6, "stock": 12})
    assert r.status_code == 201
    assert len(client.get("/inventory").get_json()) == 3


def test_import_requires_input(client):
    assert client.post("/inventory/import", json={}).status_code == 400


def test_external_api_failure(client, monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("down")
    monkeypatch.setattr(app_module.requests, "get", boom)
    assert client.get("/external/barcode/123").status_code == 502