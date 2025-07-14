#test_items.py

def test_create_item_success(client):
    payload = {
        "name": "Widget A",
        "description": "Test widget",
        "price": 10,
        "available": True,
        "email": "alice@example.com",
        "special_id": 1001
    }
    response = client.post("/items/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "id" in data
    assert response.headers["Location"].endswith(f"/items/{data['id']}")

def test_create_item_duplicate_email(client):
    # First insert
    client.post(
        "/items/",
        json={
            "name": "First",
            "description": "Desc",
            "price": 1,
            "available": True,
            "email": "bob@example.com",
            "special_id": 2002
        }
    )
    # Duplicate email
    response = client.post(
        "/items/",
        json={
            "name": "Second",
            "description": "Desc2",
            "price": 2,
            "available": False,
            "email": "bob@example.com",
            "special_id": 2003
        }
    )
    assert response.status_code == 409
    err = response.json()
    assert err["error"] == "UniqueViolation"
    assert "email" in err["message"].lower()

def test_get_nonexistent_item(client):
    response = client.get("/items/9999")
    assert response.status_code == 404
    err = response.json()
    assert err["error"] == "NotFound"
