from marshmallow import Schema, fields, validate

from .common import non_blank


class ProductIn(Schema):
    sku = fields.Str(required=True, validate=[validate.Length(min=3, max=32), non_blank])
    name = fields.Str(required=True, validate=[validate.Length(min=1, max=255), non_blank])
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(required=True, strict=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, strict=True, validate=validate.Range(min=0))


class ProductPatch(ProductIn):
    # partial=True bỏ qua cả required lẫn load_default khi PATCH.
    pass


class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()
    created_at = fields.DateTime()


class ProductPage(Schema):
    items = fields.List(fields.Nested(ProductOut))
    page = fields.Int()
    size = fields.Int()
    total = fields.Int()


class ReserveIn(Schema):
    qty = fields.Int(required=True, strict=True, validate=validate.Range(min=1))
