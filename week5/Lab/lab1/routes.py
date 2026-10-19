from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
from models import db, Book, Category
from schemas import (
    book_schema,
    books_schema,
    book_create_schema,
    book_update_schema,
    category_schema,
    categories_schema,
)
from pagination import (
    parse_query_params,
    execute_offset_pagination,
    execute_cursor_pagination,
    PaginationValidationError,
)

api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_bp.errorhandler(PaginationValidationError)
def handle_pagination_error(error: PaginationValidationError):
    return jsonify({
        "error": error.message,
        "code": error.code,
        "detail": error.message,
    }), error.status_code


@api_bp.errorhandler(ValidationError)
def handle_schema_validation_error(error: ValidationError):
    return jsonify({
        "error": "Validation failed.",
        "code": "VALIDATION_ERROR",
        "detail": error.messages,
    }), 422


@api_bp.get("/books")
def list_books():
    """
    List books with offset or cursor pagination, genre filter, and multi-key sorting.
    """
    params = parse_query_params(request.args.to_dict())

    # Build base query
    query = Book.query

    # Apply genre filtering
    if params["genre"]:
        query = query.join(Book.category).filter(
            Category.slug == params["genre"].lower()
        )

    secret_key = current_app.config.get("SECRET_KEY", "default-secret-key")

    if params["strategy"] == "offset":
        result = execute_offset_pagination(
            query=query,
            offset=params["offset"],
            limit=params["limit"],
            sort_specs=params["sort_specs"],
        )
        return jsonify({
            "data": books_schema.dump(result["items"]),
            "pagination": result["pagination"],
        }), 200

    else:  # strategy == "cursor"
        result = execute_cursor_pagination(
            query=query,
            cursor=params["cursor"],
            limit=params["limit"],
            sort_specs=params["sort_specs"],
            canonical_sort=params["canonical_sort"],
            genre=params["genre"],
            secret_key=secret_key,
        )
        return jsonify({
            "data": books_schema.dump(result["items"]),
            "page_info": result["page_info"],
        }), 200


@api_bp.post("/books")
def create_book():
    """
    Create a new book.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    data = book_create_schema.load(payload)

    # Validate category exists
    category = db.session.get(Category, data["category_id"])
    if not category:
        return jsonify({
            "error": f"Category with id {data['category_id']} not found.",
            "code": "NOT_FOUND",
            "detail": f"Category with id {data['category_id']} does not exist.",
        }), 422

    # Validate unique isbn if provided
    if data.get("isbn"):
        existing_isbn = Book.query.filter_by(isbn=data["isbn"]).first()
        if existing_isbn:
            return jsonify({
                "error": f"Book with isbn '{data['isbn']}' already exists.",
                "code": "ALREADY_EXISTS",
                "detail": f"Book with isbn '{data['isbn']}' already exists.",
            }), 422

    book = Book(
        title=data["title"],
        author=data["author"],
        isbn=data.get("isbn"),
        price_vnd=data["price_vnd"],
        category_id=data["category_id"],
    )
    db.session.add(book)
    db.session.commit()

    return jsonify(book_schema.dump(book)), 201


@api_bp.get("/books/<int:book_id>")
def get_book(book_id: int):
    """
    Get book details by ID.
    """
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({
            "error": f"Book with id {book_id} not found.",
            "code": "NOT_FOUND",
            "detail": f"Book with id {book_id} was not found.",
        }), 404
    return jsonify(book_schema.dump(book)), 200


@api_bp.put("/books/<int:book_id>")
def update_book(book_id: int):
    """
    Update book details.
    """
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({
            "error": f"Book with id {book_id} not found.",
            "code": "NOT_FOUND",
            "detail": f"Book with id {book_id} was not found.",
        }), 404

    payload = request.get_json(silent=True) or {}
    data = book_update_schema.load(payload)

    if "category_id" in data:
        cat = db.session.get(Category, data["category_id"])
        if not cat:
            return jsonify({
                "error": f"Category with id {data['category_id']} not found.",
                "code": "NOT_FOUND",
                "detail": f"Category with id {data['category_id']} does not exist.",
            }), 422
        book.category_id = data["category_id"]

    if "title" in data:
        book.title = data["title"]
    if "author" in data:
        book.author = data["author"]
    if "isbn" in data:
        if data["isbn"] and data["isbn"] != book.isbn:
            existing_isbn = Book.query.filter_by(isbn=data["isbn"]).first()
            if existing_isbn:
                return jsonify({
                    "error": f"Book with isbn '{data['isbn']}' already exists.",
                    "code": "ALREADY_EXISTS",
                    "detail": f"Book with isbn '{data['isbn']}' already exists.",
                }), 422
        book.isbn = data["isbn"]
    if "price_vnd" in data:
        book.price_vnd = data["price_vnd"]

    db.session.commit()
    return jsonify(book_schema.dump(book)), 200


@api_bp.delete("/books/<int:book_id>")
def delete_book(book_id: int):
    """
    Delete a book by ID.
    """
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({
            "error": f"Book with id {book_id} not found.",
            "code": "NOT_FOUND",
            "detail": f"Book with id {book_id} was not found.",
        }), 404

    db.session.delete(book)
    db.session.commit()
    return "", 204


@api_bp.get("/categories")
def list_categories():
    """
    List all categories.
    """
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify(categories_schema.dump(categories)), 200


@api_bp.post("/categories")
def create_category():
    """
    Create a new category.
    """
    payload = request.get_json(silent=True) or {}
    data = category_schema.load(payload)

    existing = Category.query.filter_by(slug=data["slug"]).first()
    if existing:
        return jsonify({
            "error": f"Category with slug '{data['slug']}' already exists.",
            "code": "ALREADY_EXISTS",
            "detail": f"Category with slug '{data['slug']}' already exists.",
        }), 422

    category = Category(name=data["name"], slug=data["slug"])
    db.session.add(category)
    db.session.commit()
    return jsonify(category_schema.dump(category)), 201
