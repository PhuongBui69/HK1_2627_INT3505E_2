from marshmallow import Schema, ValidationError, fields, validate


def non_blank(value):
    if not value.strip():
        raise ValidationError("Không được chỉ chứa khoảng trắng.")


class PaginationIn(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    size = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))


class ErrorSchema(Schema):
    error = fields.Str()
    detail = fields.Raw()
