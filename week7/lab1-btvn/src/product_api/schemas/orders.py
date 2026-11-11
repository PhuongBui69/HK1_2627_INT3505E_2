from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from .products import ProductOut, ReserveIn


class OrderItemIn(ReserveIn):
    product_id = fields.Int(required=True, strict=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    items = fields.List(fields.Nested(OrderItemIn), required=True, validate=validate.Length(min=1))

    @validates_schema
    def unique_products(self, data, **kwargs):
        ids = [item["product_id"] for item in data["items"]]
        if len(ids) != len(set(ids)):
            raise ValidationError("Mỗi sản phẩm chỉ xuất hiện một lần trong đơn.", "items")


class OrderItemOut(Schema):
    id = fields.Int()
    product_id = fields.Int()
    qty = fields.Int()
    unit_price_cents = fields.Int()
    product = fields.Nested(ProductOut)


class OrderOut(Schema):
    id = fields.Int()
    created_at = fields.DateTime()
    items = fields.List(fields.Nested(OrderItemOut))


class OrderPage(Schema):
    items = fields.List(fields.Nested(OrderOut))
    page = fields.Int()
    size = fields.Int()
    total = fields.Int()
