import pytest


def test_get_book_detail(client):
    """Verify GET /api/v1/books/<id> returns 200 and serialized book."""
    response = client.get("/api/v1/books/1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == 1
    assert data["title"] == "Clean Code"
    assert "price" in data
    assert "category" in data
    assert data["category"]["slug"] == "tech"


def test_get_book_not_found(client):
    """Verify GET non-existing book returns HTTP 404."""
    response = client.get("/api/v1/books/99999")
    assert response.status_code == 404
    data = response.get_json()
    assert data["code"] == "NOT_FOUND"


def test_create_book_success(client):
    """Verify POST /api/v1/books creates a new book and returns 201."""
    payload = {
        "title": "Continuous Delivery",
        "author": "Jez Humble",
        "isbn": "9780321601919",
        "price": 400000.0,
        "category_id": 1,
    }
    response = client.post("/api/v1/books", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Continuous Delivery"
    assert data["author"] == "Jez Humble"
    assert data["price"] == 400000.0
    assert data["id"] is not None

    # Verify book is present in database
    get_res = client.get(f"/api/v1/books/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.get_json()["title"] == "Continuous Delivery"


def test_create_book_invalid_category(client):
    """Verify creating a book with invalid category returns 422."""
    payload = {
        "title": "Invalid Category Book",
        "author": "Anonymous",
        "price": 100000.0,
        "category_id": 99999,
    }
    response = client.post("/api/v1/books", json=payload)
    assert response.status_code == 422
    data = response.get_json()
    assert "error" in data


def test_create_book_duplicate_isbn(client):
    """Verify creating a book with existing ISBN returns 422."""
    payload = {
        "title": "Duplicate ISBN Book",
        "author": "Some Author",
        "isbn": "9780132350884",  # Already in seed for Clean Code
        "price": 100000.0,
        "category_id": 1,
    }
    response = client.post("/api/v1/books", json=payload)
    assert response.status_code == 422
    data = response.get_json()
    assert data["code"] == "ALREADY_EXISTS"


def test_create_book_negative_price(client):
    """Verify creating a book with negative price fails schema validation."""
    payload = {
        "title": "Negative Price Book",
        "author": "Some Author",
        "price": -50.0,
        "category_id": 1,
    }
    response = client.post("/api/v1/books", json=payload)
    assert response.status_code == 422


def test_update_book(client):
    """Verify PUT /api/v1/books/<id> updates existing book."""
    update_payload = {
        "title": "Clean Code: 2nd Edition",
        "price": 380000.0,
    }
    response = client.put("/api/v1/books/1", json=update_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Clean Code: 2nd Edition"
    assert data["price"] == 380000.0


def test_update_book_not_found(client):
    """Verify PUT non-existent book returns 404."""
    response = client.put("/api/v1/books/99999", json={"title": "Updated"})
    assert response.status_code == 404


def test_delete_book(client):
    """Verify DELETE /api/v1/books/<id> removes book."""
    response = client.delete("/api/v1/books/1")
    assert response.status_code == 204

    # Subsequent GET should return 404
    get_res = client.get("/api/v1/books/1")
    assert get_res.status_code == 404


def test_delete_book_not_found(client):
    """Verify DELETE non-existent book returns 404."""
    response = client.delete("/api/v1/books/99999")
    assert response.status_code == 404


def test_list_and_create_categories(client):
    """Verify categories listing and creation."""
    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    categories = res.get_json()
    assert len(categories) >= 4

    create_res = client.post("/api/v1/categories", json={"name": "History", "slug": "history"})
    assert create_res.status_code == 201
    assert create_res.get_json()["slug"] == "history"
