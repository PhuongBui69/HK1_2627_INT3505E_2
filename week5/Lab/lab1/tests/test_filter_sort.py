import pytest


def test_genre_filter_offset(client):
    """Filter by genre=tech with offset strategy."""
    response = client.get("/api/v1/books?strategy=offset&genre=tech&limit=50")
    assert response.status_code == 200
    data = response.get_json()

    assert data["pagination"]["total"] == 15
    assert len(data["data"]) == 15
    for book in data["data"]:
        assert book["category"]["slug"] == "tech"


def test_genre_filter_cursor_traversal(client):
    """Traverse all records matching genre=science using cursor pagination."""
    science_books = []
    cursor = None

    while True:
        url = "/api/v1/books?strategy=cursor&genre=science&limit=2"
        if cursor:
            url += f"&cursor={cursor}"

        response = client.get(url)
        assert response.status_code == 200
        data = response.get_json()

        for book in data["data"]:
            assert book["category"]["slug"] == "science"
            science_books.append(book)

        if not data["page_info"]["has_more"]:
            break
        cursor = data["page_info"]["next_cursor"]

    assert len(science_books) == 5
    assert len(set(b["id"] for b in science_books)) == 5


def test_genre_nonexistent_returns_empty(client):
    """Filter by nonexistent genre returns empty list with 200 OK."""
    # Offset strategy
    r_offset = client.get("/api/v1/books?strategy=offset&genre=does_not_exist")
    assert r_offset.status_code == 200
    d_offset = r_offset.get_json()
    assert d_offset["data"] == []
    assert d_offset["pagination"]["total"] == 0
    assert d_offset["pagination"]["has_next"] is False

    # Cursor strategy
    r_cursor = client.get("/api/v1/books?strategy=cursor&genre=does_not_exist")
    assert r_cursor.status_code == 200
    d_cursor = r_cursor.get_json()
    assert d_cursor["data"] == []
    assert d_cursor["page_info"]["next_cursor"] is None
    assert d_cursor["page_info"]["has_more"] is False


def test_multi_key_sort_ascending_and_descending(client):
    """Verify sorting in ascending and descending order."""
    # Ascending price
    r_asc = client.get("/api/v1/books?sort=price&limit=30")
    assert r_asc.status_code == 200
    books_asc = r_asc.get_json()["data"]
    prices_asc = [b["price"] for b in books_asc]
    assert prices_asc == sorted(prices_asc)

    # Descending price
    r_desc = client.get("/api/v1/books?sort=-price&limit=30")
    assert r_desc.status_code == 200
    books_desc = r_desc.get_json()["data"]
    prices_desc = [b["price"] for b in books_desc]
    assert prices_desc == sorted(prices_desc, reverse=True)


def test_multi_key_sort_combined_fields(client):
    """Verify combined sort -price,title."""
    response = client.get("/api/v1/books?sort=-price,title&limit=30")
    assert response.status_code == 200
    books = response.get_json()["data"]

    for i in range(len(books) - 1):
        b1 = books[i]
        b2 = books[i + 1]
        if b1["price"] == b2["price"]:
            assert b1["title"] <= b2["title"]
        else:
            assert b1["price"] > b2["price"]


@pytest.mark.parametrize(
    "malicious_or_invalid_sort",
    [
        "unknown_field",
        "drop_table",
        "title; DROP TABLE books;--",
        "1 UNION SELECT * FROM books",
        "price,",
        ",",
        "-",
        "--price",
    ],
)
def test_invalid_sort_fields_rejected_400(client, malicious_or_invalid_sort):
    """Ensure invalid sort fields and injection attempts are rejected with HTTP 400."""
    response = client.get(f"/api/v1/books?sort={malicious_or_invalid_sort}")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_combined_genre_filter_sort_and_offset(client):
    """Combine genre=fiction, sort=-price, offset pagination."""
    # Page 1: limit 3
    r1 = client.get("/api/v1/books?strategy=offset&genre=fiction&sort=-price&limit=3&offset=0")
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1["pagination"]["total"] == 5
    assert len(d1["data"]) == 3
    assert d1["pagination"]["has_next"] is True

    # Page 2: offset 3, limit 3
    r2 = client.get("/api/v1/books?strategy=offset&genre=fiction&sort=-price&limit=3&offset=3")
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert len(d2["data"]) == 2
    assert d2["pagination"]["has_next"] is False

    # Check descending order maintained
    all_fiction_prices = [b["price"] for b in d1["data"] + d2["data"]]
    assert all_fiction_prices == sorted(all_fiction_prices, reverse=True)
