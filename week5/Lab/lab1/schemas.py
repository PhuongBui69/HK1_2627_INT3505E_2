from marshmallow import Schema, fields, validate


class CategorySchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    slug = fields.String(required=True, validate=validate.Length(min=1, max=100))


class BookSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    author = fields.String(required=True, validate=validate.Length(min=1, max=255))
    isbn = fields.String(allow_none=True, validate=validate.Length(max=20))
    price = fields.Float(attribute="price_vnd", dump_only=True)
    category = fields.Nested(CategorySchema, dump_only=True)


class BookCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    author = fields.String(required=True, validate=validate.Length(min=1, max=255))
    isbn = fields.String(allow_none=True, load_default=None)
    price_vnd = fields.Float(data_key="price", required=True, validate=validate.Range(min=0))
    category_id = fields.Integer(required=True)


class BookUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=1, max=255))
    author = fields.String(validate=validate.Length(min=1, max=255))
    isbn = fields.String(allow_none=True)
    price_vnd = fields.Float(data_key="price", validate=validate.Range(min=0))
    category_id = fields.Integer()


category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
book_schema = BookSchema()
books_schema = BookSchema(many=True)
book_create_schema = BookCreateSchema()
book_update_schema = BookUpdateSchema()
