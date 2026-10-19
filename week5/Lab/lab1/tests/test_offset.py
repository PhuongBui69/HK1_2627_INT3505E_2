import pytest


def test_offset_pagination_defaults(client):
    """Verify default query uses offset strategy, limit 20, offset 0."""
    response = client.get("/api/v1/books")
    assert response.status_code == 200
    data = response.get_json()

    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) == 20

    pagination = data["pagination"]
    assert pagination["strategy"] == "offset"
    assert pagination["offset"] == 0
    assert pagination["limit"] == 20
    assert pagination["total"] == 30
    assert pagination["has_next"] is True


def test_offset_pagination_explicit_pages(client):
    """Verify paging across multiple pages with distinct records."""
    # Page 1: 10 items
    r1 = client.get("/api/v1/books?strategy=offset&offset=0&limit=10")
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert len(d1["data"]) == 10
    assert d1["pagination"]["has_next"] is True
    ids_page1 = [b["id"] for b in d1["data"]]

    # Page 2: next 10 items
    r2 = client.get("/api/v1/books?strategy=offset&offset=10&limit=10")
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert len(d2["data"]) == 10
    assert d2["pagination"]["has_next"] is True
    ids_page2 = [b["id"] for b in d2["data"]]

    # Page 3: last 10 items
    r3 = client.get("/api/v1/books?strategy=offset&offset=20&limit=10")
    assert r3.status_code == 200
    d3 = r3.get_json()
    assert len(d3["data"]) == 10
    assert d3["pagination"]["has_next"] is False
    ids_page3 = [b["id"] for b in d3["data"]]

    # Ensure no overlap
    assert len(set(ids_page1).intersection(set(ids_page2))) == 0
    assert len(set(ids_page2).intersection(set(ids_page3))) == 0
    assert len(set(ids_page1).intersection(set(ids_page3))) == 0


def test_offset_beyond_total(client):
    """Verify querying offset beyond total count returns empty list and has_next=False."""
    response = client.get("/api/v1/books?strategy=offset&offset=100&limit=10")
    assert response.status_code == 200
    data = response.get_json()
    assert data["data"] == []
    assert data["pagination"]["offset"] == 100
    assert data["pagination"]["total"] == 30
    assert data["pagination"]["has_next"] is False


def test_offset_limit_boundaries(client):
    """Verify minimum limit (1) and maximum limit (100)."""
    r_min = client.get("/api/v1/books?limit=1")
    assert r_min.status_code == 200
    assert len(r_min.get_json()["data"]) == 1

    r_max = client.get("/api/v1/books?limit=100")
    assert r_max.status_code == 200
    assert len(r_max.get_json()["data"]) == 30
    assert r_max.get_json()["pagination"]["has_next"] is False


@pytest.mark.parametrize("invalid_limit", [0, -1, -50, 101, 200, "abc", ""])
def test_invalid_limit_returns_400(client, invalid_limit):
    """Verify invalid limit parameter returns HTTP 400."""
    response = client.get(f"/api/v1/books?limit={invalid_limit}")
    if invalid_limit == "":
        # empty limit defaults to 20
        assert response.status_code == 200
    else:
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


@pytest.mark.parametrize("invalid_offset", [-1, -100, "abc", "1.5"])
def test_invalid_offset_returns_400(client, invalid_offset):
    """Verify negative or non-integer offset returns HTTP 400."""
    response = client.get(f"/api/v1/books?offset={invalid_offset}")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_invalid_strategy_returns_400(client):
    """Verify unsupported strategy returns HTTP 400."""
    response = client.get("/api/v1/books?strategy=keyset_invalid")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Unsupported strategy" in data["error"]
