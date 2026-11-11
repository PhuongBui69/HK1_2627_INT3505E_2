from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...extensions import db

if TYPE_CHECKING:
    from .order import Order
    from .product import Product


class OrderItem(db.Model):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_product"),
        CheckConstraint("qty > 0", name="ck_order_item_qty"),
        CheckConstraint("unit_price_cents >= 0", name="ck_order_item_price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    qty: Mapped[int]
    unit_price_cents: Mapped[int]
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
