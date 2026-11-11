from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...extensions import db
from ..models import Order, OrderItem
from .pagination import paginate


def _with_items():
    # Eager loading nằm tại nơi tạo query, trước khi serialize response.
    return select(Order).options(selectinload(Order.items).selectinload(OrderItem.product))


def list_with_items(page, size):
    return paginate(_with_items(), Order, page, size)


def find_with_items(order_id):
    return db.session.scalar(_with_items().where(Order.id == order_id))


def add(order):
    db.session.add(order)
