# fastapi_postgres_app/tests/test_items_extended.py

import pytest
from fastapi.testclient import TestClient

from fastapi_postgres_app.main import app


def get_token(client: TestClient, perms: str = "full_access", mins: int = 5) -> str:
    resp = client.post("/token", json={"permissions": perms, "expires_minutes": mins})
    assert resp.status_code == 200
    return resp.json()["access_token"]


#
# 1. PUT & PATCH Update Flows
#
def test_full_update_item_success(client: TestClient):
    payload = {
        "name": "A", "description": "Desc A", "price": 10,
        "available": True, "email": "a@x.com", "special_id": 111
    }
    res = client.post("/items/", json=payload)
    assert res.status_code == 201
    item_id = res.json()["id"]

    updated = {
        "name": "A+", "description": "Desc B", "price": 20,
        "available": False, "email": "b@x.com", "special_id": 222
    }
    res2 = client.put(f"/items/{item_id}", json=updated)
    assert res2.status_code == 200
    for k, v in updated.items():
        assert res2.json()[k] == v


def test_partial_update_item_success(client: TestClient):
    payload = {
        "name": "C", "description": "Desc C", "price": 30,
        "available": True, "email": "c@x.com", "special_id": 333
    }
    res = client.post("/items/", json=payload)
    item_id = res.json()["id"]

    patch = {"price": 99}
    res2 = client.patch(f"/items/{item_id}", json=patch)
    assert res2.status_code == 200
    assert res2.json()["price"] == 99
    assert res2.json()["name"] == payload["name"]


@pytest.mark.parametrize("dup_field,dup_value", [
    ("email", "dup@x.com"),
    ("special_id", 400),
])
def test_update_duplicate_field(client: TestClient, dup_field, dup_value):
    i1 = {"name": "X", "description": "D", "price": 1, "available": True,
          "email": "dup@x.com", "special_id": 400}
    i2 = {"name": "Y", "description": "D", "price": 2, "available": True,
          "email": "uniq@x.com", "special_id": 500}
    client.post("/items/", json=i1)
    r2 = client.post("/items/", json=i2)
    id2 = r2.json()["id"]

    patch = {dup_field: dup_value}
    resp = client.patch(f"/items/{id2}", json=patch)
    assert resp.status_code == 409
    assert resp.json()["error"] == "UniqueViolation"


def test_update_missing_item_returns_404(client: TestClient):
    resp = client.patch("/items/999999", json={"price": 77})
    assert resp.status_code == 404
    assert resp.json()["error"] == "NotFound"


def test_put_missing_item_returns_404(client: TestClient):
    resp = client.put("/items/999999", json={
        "name": "Z", "description": "D", "price": 5, "available": False,
        "email": "z@x.com", "special_id": 999
    })
    assert resp.status_code == 404
    assert resp.json()["error"] == "NotFound"


#
# 2. DELETE Operations
#
def test_delete_existing_item(client: TestClient):
    item = {"name": "D", "description": "Desc", "price": 5, "available": True,
            "email": "del@x.com", "special_id": 600}
    rid = client.post("/items/", json=item).json()["id"]

    res = client.delete(f"/items/{rid}")
    assert res.status_code == 204


def test_delete_missing_item_returns_404(client: TestClient):
    res = client.delete("/items/111111")
    assert res.status_code == 404
    assert res.json()["error"] == "NotFound"


def test_delete_idempotency(client: TestClient):
    item = {"name": "E", "description": "Desc", "price": 6, "available": True,
            "email": "e@x.com", "special_id": 700}
    rid = client.post("/items/", json=item).json()["id"]

    r1 = client.delete(f"/items/{rid}")
    r2 = client.delete(f"/items/{rid}")
    assert r1.status_code == 204
    assert r2.status_code == 404


#
# 3. Query Filters on GET /items/
#
def test_query_filters(client: TestClient):
    items = [
        {"name": "F", "description": "foo", "price": 10, "available": True,
         "email": "f@x.com", "special_id": 800},
        {"name": "G", "description": "goo", "price": 20, "available": False,
         "email": "g@x.com", "special_id": 801},
        {"name": "Widget", "description": "widget", "price": 30, "available": True,
         "email": "h@x.com", "special_id": 802},
    ]
    for it in items:
        client.post("/items/", json=it)

    r_avail = client.get("/items/?available=true")
    assert all(i["available"] for i in r_avail.json())

    r_lt = client.get("/items/?price_lt=25")
    assert all(i["price"] < 25 for i in r_lt.json())

    r_gt = client.get("/items/?price_gt=15")
    assert all(i["price"] > 15 for i in r_gt.json())

    r_s = client.get("/items/?search=widgEt")
    assert len(r_s.json()) == 1 and r_s.json()[0]["name"] == "Widget"

    r_comb = client.get("/items/?available=true&price_lt=20")
    assert all(i["available"] and i["price"] < 20 for i in r_comb.json())


#
# 4. Validation & Edge Cases (422 errors)
#
@pytest.mark.parametrize("payload,missing", [
    ({}, ["name", "description", "email", "special_id"]),
    ({"name": "A"}, ["description", "email", "special_id"]),
])
def test_missing_required_fields_422(client: TestClient, payload, missing):
    resp = client.post("/items/", json=payload)
    assert resp.status_code == 422
    for field in missing:
        assert any(err["loc"][-1] == field for err in resp.json()["detail"])


def test_invalid_types_422(client: TestClient):
    bad = {
        "name": 123, "description": True, "price": "free",
        "available": "yes", "email": "notanemail", "special_id": "sid"
    }
    resp = client.post("/items/", json=bad)
    assert resp.status_code == 422


def test_extra_fields_422(client: TestClient):
    extra = {
        "name": "X", "description": "D", "price": 1, "available": True,
        "email": "x@x.com", "special_id": 900, "oops": "nope"
    }
    resp = client.post("/items/", json=extra)
    assert resp.status_code == 422


def test_negative_price_422(client: TestClient):
    neg = {
        "name": "N", "description": "D", "price": -5,
        "available": True, "email": "n@x.com", "special_id": 901
    }
    resp = client.post("/items/", json=neg)
    assert resp.status_code == 422


#
# 5. Authentication Guards (401 & 403)
#
def test_missing_token_returns_401(auth_client: TestClient):
    res = auth_client.get("/items/")
    assert res.status_code == 401


def test_insufficient_permission_returns_403(auth_client: TestClient):
    token = get_token(auth_client, perms="read_only")
    headers = {"Authorization": f"Bearer {token}"}
    res = auth_client.post(
        "/items/", headers=headers, json={
            "name": "X", "description": "D", "price": 1,
            "available": True, "email": "p@x.com", "special_id": 950
        }
    )
    assert res.status_code == 403


def test_full_access_token_allows_write(auth_client: TestClient):
    token = get_token(auth_client, perms="full_access")
    headers = {"Authorization": f"Bearer {token}"}
    res = auth_client.post(
        "/items/", headers=headers, json={
            "name": "Z", "description": "D", "price": 1,
            "available": True, "email": "z@x.com", "special_id": 951
        }
    )
    assert res.status_code == 201


#
# 6. Sequential Conflict Simulation
#
def test_sequential_duplicate_special_id(client: TestClient):
    base = {
        "name": "C1",
        "description": "D",
        "price": 5,
        "available": True,
        "email": "dup1@x.com",
        "special_id": 960,
    }
    r1 = client.post("/items/", json=base)
    r2 = client.post("/items/", json=base)
    assert r1.status_code == 201
    assert r2.status_code == 409
    assert r2.json()["error"] == "UniqueViolation"
