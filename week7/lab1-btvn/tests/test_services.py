import pytest

from product_api.exceptions.business import OutOfStockError
from product_api.services import orders, products


def test_service_rolls_back_without_http_handler(app):
    # Gọi service trực tiếp: rollback không được phụ thuộc global HTTP handler.
    with app.app_context():
        first = products.create_product({"sku": "BOOK-01", "name": "Book", "price_cents": 1000,
                                         "qty_in_stock": 10})
        second = products.create_product({"sku": "PEN-01", "name": "Pen", "price_cents": 500,
                                          "qty_in_stock": 1})
        first_id, second_id = first.id, second.id
        with pytest.raises(OutOfStockError):
            orders.create_order([
                {"product_id": first_id, "qty": 2},
                {"product_id": second_id, "qty": 2},
            ])

        assert products.get_product(first_id).qty_in_stock == 10
        assert orders.list_orders(page=1, size=20)["total"] == 0
        # Session vẫn dùng được cho transaction kế tiếp.
        order = orders.create_order([{"product_id": first_id, "qty": 2}])
        assert len(order.items) == 1
        assert products.get_product(first_id).qty_in_stock == 8
