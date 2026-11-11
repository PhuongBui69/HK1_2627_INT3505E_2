import pytest

from product_api.extensions import db
from product_api.persistence.models import Product

URL = "/api/v1/products"


def test_post_product_persists_and_defaults_stock(app, client, product_data):
    product_data.pop("qty_in_stock")
    response = client.post(URL, json=product_data)
    assert response.status_code == 201
    body = response.get_json()
    assert body["sku"] == "BOOK-01"
    assert body["qty_in_stock"] == 0
    assert body["archived"] is False
    with app.app_context():
        assert db.session.get(Product, body["id"]).name == "Sách SOA"


def test_duplicate_sku_and_session_rollback(client, product, product_data):
    response = client.post(URL, json=product_data)
    assert response.status_code == 409
    assert response.get_json()["error"] == "conflict"
    product_data["sku"] = "BOOK-02"
    assert client.post(URL, json=product_data).status_code == 201


@pytest.mark.parametrize("changes", [
    {"sku": "ab"}, {"sku": "x" * 33}, {"name": ""}, {"name": "   "},
    {"name": "x" * 256}, {"price_cents": -1}, {"price_cents": 1.5},
    {"price_cents": True}, {"qty_in_stock": -1}, {"unknown": 1},
])
def test_invalid_product_returns_422(client, product_data, changes):
    response = client.post(URL, json={**product_data, **changes})
    assert response.status_code == 422
    assert set(response.get_json()) == {"error", "detail"}


def test_malformed_json_and_missing_content_type(client):
    assert client.post(URL, data="{bad", content_type="application/json").status_code == 400
    assert client.post(URL, data="{}").status_code == 400


def test_list_pagination_and_soft_delete(app, client, product, product_data):
    for index in range(2, 4):
        client.post(URL, json={**product_data, "sku": f"BOOK-0{index}"})
    response = client.get(f"{URL}?page=2&size=1")
    assert response.status_code == 200
    body = response.get_json()
    assert (body["page"], body["size"], body["total"]) == (2, 1, 3)
    assert len(body["items"]) == 1
    assert body["items"][0]["sku"] == "BOOK-02"

    path = f"{URL}/{product['id']}"
    response = client.delete(path)
    assert response.status_code == 204
    assert response.data == b""
    assert client.get(path).status_code == 404
    assert client.patch(path, json={"name": "New"}).status_code == 404
    assert client.post(path + "/reserve", json={"qty": 1}).status_code == 404
    body = client.get(URL).get_json()
    assert body["total"] == 2
    assert all(item["id"] != product["id"] for item in body["items"])
    with app.app_context():
        assert db.session.get(Product, product["id"]).archived is True


@pytest.mark.parametrize("query", ["page=0", "page=abc", "size=0", "size=101"])
def test_invalid_pagination(client, query):
    assert client.get(f"{URL}?{query}").status_code == 422


def test_patch_changes_only_supplied_fields(client, product):
    path = f"{URL}/{product['id']}"
    response = client.patch(path, json={"name": "Tên mới"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "Tên mới"
    for key in ("sku", "price_cents", "qty_in_stock"):
        assert body[key] == product[key]
    assert client.patch(path, json={"price_cents": -1}).status_code == 422
    assert client.get(path).get_json()["price_cents"] == product["price_cents"]


def test_reserve_does_not_allow_negative_stock(client, product):
    path = f"{URL}/{product['id']}"
    assert client.post(path + "/reserve", json={"qty": 4}).get_json()["qty_in_stock"] == 6
    assert client.post(path + "/reserve", json={"qty": 7}).status_code == 409
    assert client.get(path).get_json()["qty_in_stock"] == 6
    assert client.post(path + "/reserve", json={"qty": 6}).get_json()["qty_in_stock"] == 0
    assert client.post(path + "/reserve", json={"qty": 1}).status_code == 409
    assert client.post(path + "/reserve", json={"qty": 0}).status_code == 422


def test_missing_product(client):
    response = client.get(f"{URL}/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "not_found"
