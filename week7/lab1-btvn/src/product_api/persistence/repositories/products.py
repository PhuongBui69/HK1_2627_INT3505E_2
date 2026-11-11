from sqlalchemy import select, update

from ...extensions import db
from ..models import Product
from .pagination import paginate


def list_active(page, size):
    return paginate(select(Product).where(Product.archived.is_(False)), Product, page, size)


def find_active(product_id):
    return db.session.scalar(
        select(Product).where(Product.id == product_id, Product.archived.is_(False))
    )


def find_active_by_ids(product_ids):
    return db.session.scalars(
        select(Product).where(Product.id.in_(product_ids), Product.archived.is_(False))
    ).all()


def add(product):
    db.session.add(product)


def decrease_stock(product_id, qty):
    # Kiểm tra và trừ tồn kho trong cùng UPDATE, không có lúc ghi số âm.
    result = db.session.execute(
        update(Product)
        .where(Product.id == product_id, Product.archived.is_(False), Product.qty_in_stock >= qty)
        .values(qty_in_stock=Product.qty_in_stock - qty)
    )
    return result.rowcount == 1
