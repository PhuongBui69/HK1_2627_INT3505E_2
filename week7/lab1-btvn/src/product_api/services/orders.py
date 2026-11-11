from ..exceptions.business import NotFoundError
from ..persistence.models import Order, OrderItem
from ..persistence.repositories import orders as order_repository
from ..persistence.repositories import products as product_repository
from ..persistence.transaction import transaction
from .products import decrease_stock


def list_orders(page, size):
    return order_repository.list_with_items(page, size)


def get_order(order_id):
    order = order_repository.find_with_items(order_id)
    if order is None:
        raise NotFoundError("Không tìm thấy đơn hàng.")
    return order


def create_order(items):
    with transaction():
        products = product_repository.find_active_by_ids([item["product_id"] for item in items])
        by_id = {product.id: product for product in products}
        if len(by_id) != len(items):
            raise NotFoundError("Có sản phẩm không tồn tại hoặc đã bị xóa.")

        order = Order()
        for item in items:
            product = by_id[item["product_id"]]
            decrease_stock(product.id, item["qty"])
            order.items.append(OrderItem(
                product=product, qty=item["qty"], unit_price_cents=product.price_cents
            ))
        order_repository.add(order)
    # Commit một lần cho cả đơn; bất kỳ item nào lỗi đều rollback toàn bộ.
    return get_order(order.id)
