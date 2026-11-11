from contextlib import contextmanager

import pytest
from sqlalchemy import event, func, select

from product_api.extensions import db
from product_api.persistence.models import Order, OrderItem, Product

URL = "/api/v1/orders"


def test_post_order_with_multiple_products(app, client, product, product_data):
    second = client.post("/api/v1/products", json={**product_data, "sku": "BOOK-02"}).get_json()
    response = client.post(URL, json={"items": [
        {"product_id": product["id"], "qty": 2}, {"product_id": second["id"], "qty": 3},
    ]})
    assert response.status_code == 201
    order = response.get_json()
    assert len(order["items"]) == 2
    assert {item["product_id"] for item in order["items"]} == {product["id"], second["id"]}
    assert order["items"][0]["unit_price_cents"] == product["price_cents"]
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(OrderItem)) == 2
        assert db.session.get(Product, product["id"]).qty_in_stock == 8
        assert db.session.get(Product, second["id"]).qty_in_stock == 7

    # Giá khi mua được giữ lại; soft delete không phá vỡ lịch sử đơn.
    path = f"/api/v1/products/{product['id']}"
    client.patch(path, json={"price_cents": 20000})
    client.delete(path)
    detail = client.get(f"{URL}/{order['id']}").get_json()
    assert detail["items"][0]["unit_price_cents"] == product["price_cents"]
    assert detail["items"][0]["product"]["archived"] is True


def test_order_failure_rolls_back_all_stock(app, client, product, product_data):
    second = client.post("/api/v1/products", json={**product_data, "sku": "BOOK-02"}).get_json()
    response = client.post(URL, json={"items": [
        {"product_id": product["id"], "qty": 2}, {"product_id": second["id"], "qty": 11},
    ]})
    assert response.status_code == 409
    with app.app_context():
        assert db.session.get(Product, product["id"]).qty_in_stock == 10
        assert db.session.get(Product, second["id"]).qty_in_stock == 10
        assert db.session.scalar(select(func.count()).select_from(Order)) == 0
        assert db.session.scalar(select(func.count()).select_from(OrderItem)) == 0


@pytest.mark.parametrize("payload", [
    {}, {"items": []}, {"items": [{"product_id": 1, "qty": 0}]},
    {"items": [{"product_id": 1, "qty": 1}, {"product_id": 1, "qty": 2}]},
])
def test_invalid_order(client, payload):
    assert client.post(URL, json=payload).status_code == 422


def test_order_rejects_missing_or_archived_product(client, product):
    assert client.post(URL, json={"items": [{"product_id": 999, "qty": 1}]}).status_code == 404
    client.delete(f"/api/v1/products/{product['id']}")
    assert client.post(URL, json={"items": [{"product_id": product["id"], "qty": 1}]}).status_code == 404
    assert client.get(f"{URL}/999").status_code == 404


@contextmanager
def count_selects(engine):
    statements = []

    def collect(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", collect)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", collect)


@pytest.mark.parametrize("order_count", [1, 5])
def test_get_orders_eager_loading_has_constant_query_count(app, client, order_count):
    # Mỗi đơn dùng các product khác nhau để identity map không che giấu N+1.
    with app.app_context():
        for index in range(order_count):
            order = Order()
            for offset in range(2):
                product = Product(sku=f"SKU-{index}-{offset}", name="Book", price_cents=1000)
                order.items.append(OrderItem(product=product, qty=1, unit_price_cents=1000))
            db.session.add(order)
        db.session.commit()
        engine = db.engine
    # Request bắt đầu ở app context mới, không tái sử dụng session seed.
    with count_selects(engine) as statements:
        response = client.get(URL)
    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == order_count
    assert len(body["items"]) == order_count
    assert all(len(order["items"]) == 2 for order in body["items"])
    assert all(item["product"]["name"] == "Book" for order in body["items"] for item in order["items"])
    # COUNT + orders + order_items + products = 4, không tăng theo số đơn.
    assert len(statements) == 4, statements

    with count_selects(engine) as statements:
        response = client.get(f"{URL}/{body['items'][0]['id']}")
    assert response.status_code == 200
    assert len(response.get_json()["items"]) == 2
    assert len(statements) == 3, statements
