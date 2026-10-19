import pytest


def test_cursor_first_page_structure(client):
    """Verify response structure of the first page under cursor pagination."""
    response = client.get("/api/v1/books?strategy=cursor&limit=10")
    assert response.status_code == 200
    data = response.get_json()

    assert "data" in data
    assert "page_info" in data
    assert len(data["data"]) == 10

    page_info = data["page_info"]
    assert page_info["has_more"] is True
    assert page_info["next_cursor"] is not None
    assert isinstance(page_info["next_cursor"], str)


def test_cursor_full_traversal_no_duplicates_no_omissions(client):
    """
    Traverse the entire collection of 30 books using limit=7.
    Ensure every single book is visited exactly once without duplicates or omissions.
    """
    seen_ids = []
    cursor = None
    page_count = 0

    while True:
        url = "/api/v1/books?strategy=cursor&limit=7"
        if cursor:
            url += f"&cursor={cursor}"

        response = client.get(url)
        assert response.status_code == 200
        data = response.get_json()

        items = data["data"]
        page_info = data["page_info"]
        page_count += 1

        for item in items:
            seen_ids.append(item["id"])

        if not page_info["has_more"]:
            assert page_info["next_cursor"] is None
            break

        cursor = page_info["next_cursor"]
        assert cursor is not None

    # Verify total visited
    assert len(seen_ids) == 30
    assert len(set(seen_ids)) == 30  # No duplicates
    assert set(seen_ids) == set(range(1, 31))  # All books 1..30 visited
    assert page_count == 5  # 7 + 7 + 7 + 7 + 2 = 30 across 5 pages


def test_cursor_tie_breaker_duplicate_prices(client):
    """
    Multiple books share identical prices (e.g., 350000, 250000).
    Verify that sorting by price properly handles ties without duplicating or dropping items.
    """
    seen_ids = []
    cursor = None

    while True:
        url = "/api/v1/books?strategy=cursor&sort=price&limit=4"
        if cursor:
            url += f"&cursor={cursor}"

        response = client.get(url)
        assert response.status_code == 200
        data = response.get_json()

        for item in data["data"]:
            seen_ids.append(item["id"])

        if not data["page_info"]["has_more"]:
            break
        cursor = data["page_info"]["next_cursor"]

    assert len(seen_ids) == 30
    assert len(set(seen_ids)) == 30


def test_cursor_multi_key_sorting_traversal(client):
    """
    Sort by -price,title.
    Verify all books are visited in strict multi-key order.
    """
    all_books = []
    cursor = None

    while True:
        url = "/api/v1/books?strategy=cursor&sort=-price,title&limit=6"
        if cursor:
            url += f"&cursor={cursor}"

        response = client.get(url)
        assert response.status_code == 200
        data = response.get_json()

        all_books.extend(data["data"])

        if not data["page_info"]["has_more"]:
            break
        cursor = data["page_info"]["next_cursor"]

    assert len(all_books) == 30
    # Verify strict descending price, then ascending title, then ascending id
    for i in range(len(all_books) - 1):
        curr = all_books[i]
        nxt = all_books[i + 1]

        # Order condition: (curr.price > nxt.price) OR (curr.price == nxt.price AND curr.title <= nxt.title)
        assert (
            curr["price"] > nxt["price"]
            or (curr["price"] == nxt["price"] and curr["title"] <= nxt["title"])
        ), f"Ordering violated between #{curr['id']} ({curr['price']}, {curr['title']}) and #{nxt['id']} ({nxt['price']}, {nxt['title']})"


def test_cursor_empty_string_returns_400(client):
    """Passing cursor='' returns HTTP 400."""
    response = client.get("/api/v1/books?strategy=cursor&cursor=")
    assert response.status_code == 400
    data = response.get_json()
    assert "cursor" in data["error"].lower()


def test_cursor_corrupted_token_returns_400(client):
    """Passing malformed or tampered cursor token returns HTTP 400."""
    response = client.get("/api/v1/books?strategy=cursor&cursor=gibberish_token_12345")
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid cursor" in data["error"]


def test_cursor_tampered_signature_returns_400(client):
    """Tampering with a valid cursor token signature returns HTTP 400."""
    # Obtain valid cursor
    r = client.get("/api/v1/books?strategy=cursor&limit=5")
    cursor = r.get_json()["page_info"]["next_cursor"]

    # Tamper with the last character
    tampered = cursor[:-2] + ("x" if cursor[-2] != "x" else "y") + cursor[-1]
    response = client.get(f"/api/v1/books?strategy=cursor&cursor={tampered}")
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid cursor" in data["error"]


def test_cursor_mismatch_sort_returns_400(client):
    """Using a cursor generated for sort=title with sort=-price returns HTTP 400."""
    r = client.get("/api/v1/books?strategy=cursor&sort=title&limit=5")
    cursor = r.get_json()["page_info"]["next_cursor"]

    # Request with different sort
    response = client.get(f"/api/v1/books?strategy=cursor&sort=-price&cursor={cursor}")
    assert response.status_code == 400
    data = response.get_json()
    assert "does not match" in data["error"]


def test_cursor_mismatch_genre_returns_400(client):
    """Using a cursor generated for genre=tech with genre=science returns HTTP 400."""
    r = client.get("/api/v1/books?strategy=cursor&genre=tech&limit=5")
    cursor = r.get_json()["page_info"]["next_cursor"]

    # Request with different genre
    response = client.get(f"/api/v1/books?strategy=cursor&genre=science&cursor={cursor}")
    assert response.status_code == 400
    data = response.get_json()
    assert "does not match" in data["error"]
