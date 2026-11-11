"""Lab 1, step 1: four API behavior tests.

The client fixture provides a fresh database for every test.
"""

def test_list_books_empty_database(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == []


def test_get_nonexistent_book(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["code"] == "NOT_FOUND"


def test_create_book_missing_title(client):
    response = client.post("/books", json={"author": "J.J. Geewax"})

    assert response.status_code == 400
    assert response.is_json
    payload = response.get_json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert any(error["field"] == "title" for error in payload["errors"])


def test_get_deleted_book(client):
    created = client.post(
        "/books", json={"title": "API Design Patterns", "author": "J.J. Geewax"}
    )
    assert created.status_code == 201
    book_url = f"/books/{created.get_json()['id']}"

    deleted = client.delete(book_url)
    assert deleted.status_code == 204
    assert deleted.data == b""

    response = client.get(book_url)
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"
