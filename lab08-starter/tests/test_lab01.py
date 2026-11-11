"""Lab 1: four API behavior tests and the response-schema bonus.

The client fixture provides a fresh database for every test.
"""
import pytest
from jsonschema import ValidationError, validate

from tools import get_book_schema


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


def test_response_extra_field_blocked(client):
    # Non-null values avoid OpenAPI 3.0's nullable keyword, which jsonschema
    # does not interpret as allowing JSON null.
    created = client.post("/books", json={
        "title": "API Design Patterns",
        "author": "J.J. Geewax",
        "year": 2021,
        "isbn": "9781617295850",
    })
    assert created.status_code == 201

    response = client.get(f"/books/{created.get_json()['id']}")
    assert response.status_code == 200
    payload = response.get_json()
    schema = get_book_schema()

    # First verify that the actual API response satisfies the contract.
    validate(instance=payload, schema=schema)
    assert "password_hash" not in payload

    # Simulate a leak in a copy without modifying the actual response.
    leaked_payload = {**payload, "password_hash": "fake_hash_for_testing"}
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=leaked_payload, schema=schema)

    # The rejection must be caused by the extra field, not another schema error.
    assert exc_info.value.validator == "additionalProperties"
    assert "password_hash" in exc_info.value.message
    assert "password_hash" not in payload
