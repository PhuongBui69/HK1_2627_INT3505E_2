from itsdangerous import URLSafeSerializer, BadSignature, BadData
from sqlalchemy import and_, or_
from models import Book

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MIN_LIMIT = 1
DEFAULT_OFFSET = 0
DEFAULT_STRATEGY = "offset"
VALID_STRATEGIES = {"offset", "cursor"}

# Whitelist: public_name -> (SQLAlchemy Column, model_attribute_name)
SORT_FIELD_MAP = {
    "id": (Book.id, "id"),
    "title": (Book.title, "title"),
    "author": (Book.author, "author"),
    "isbn": (Book.isbn, "isbn"),
    "price": (Book.price_vnd, "price_vnd"),
}


class PaginationValidationError(Exception):
    def __init__(self, message: str, code: str = "INVALID_ARGUMENT", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def parse_query_params(args: dict) -> dict:
    """
    Parse and validate pagination, filtering, and sorting parameters.
    Returns a normalized dictionary.
    """
    # 1. Strategy
    strategy = args.get("strategy", DEFAULT_STRATEGY)
    if strategy not in VALID_STRATEGIES:
        raise PaginationValidationError(
            f"Unsupported strategy '{strategy}'. Allowed strategies are 'offset' and 'cursor'."
        )

    # 2. Limit
    raw_limit = args.get("limit")
    if raw_limit is None or raw_limit == "":
        limit = DEFAULT_LIMIT
    else:
        try:
            limit = int(raw_limit)
        except (ValueError, TypeError):
            raise PaginationValidationError("Parameter 'limit' must be an integer.")
        if limit < MIN_LIMIT or limit > MAX_LIMIT:
            raise PaginationValidationError(
                f"Parameter 'limit' must be between {MIN_LIMIT} and {MAX_LIMIT}."
            )

    # 3. Offset
    raw_offset = args.get("offset")
    if raw_offset is None or raw_offset == "":
        offset = DEFAULT_OFFSET
    else:
        try:
            offset = int(raw_offset)
        except (ValueError, TypeError):
            raise PaginationValidationError("Parameter 'offset' must be an integer.")
        if offset < 0:
            raise PaginationValidationError("Parameter 'offset' must be a non-negative integer.")

    # 4. Cursor
    cursor = args.get("cursor")
    if cursor is not None and cursor.strip() == "":
        raise PaginationValidationError("Parameter 'cursor' cannot be empty.")

    # 5. Genre
    genre = args.get("genre")
    if genre is not None:
        genre = genre.strip()
        if not genre:
            genre = None

    # 6. Sort
    raw_sort = args.get("sort")
    sort_specs, canonical_sort = parse_sort_param(raw_sort)

    return {
        "strategy": strategy,
        "limit": limit,
        "offset": offset,
        "cursor": cursor,
        "genre": genre,
        "sort_specs": sort_specs,
        "canonical_sort": canonical_sort,
    }


def parse_sort_param(raw_sort: str | None) -> tuple[list[dict], str]:
    """
    Parse sort parameter (e.g., '-price,title').
    Ensures allowed fields, proper directions, and injects 'id' tie-breaker if absent.
    Returns (sort_specs, canonical_sort_string).
    """
    if raw_sort is None or raw_sort.strip() == "":
        raw_fields = ["id"]
    else:
        raw_fields = raw_sort.split(",")

    sort_specs = []
    seen_fields = set()
    canonical_parts = []

    for field_str in raw_fields:
        field_str = field_str.strip()
        if not field_str:
            raise PaginationValidationError("Invalid sort syntax: empty sort field.")

        if field_str.startswith("-"):
            direction = "desc"
            field_name = field_str[1:].strip()
        else:
            direction = "asc"
            field_name = field_str

        if not field_name:
            raise PaginationValidationError("Invalid sort syntax: missing field name after '-'.")

        if field_name not in SORT_FIELD_MAP:
            raise PaginationValidationError(
                f"Invalid sort field '{field_name}'. Allowed fields: {', '.join(sorted(SORT_FIELD_MAP.keys()))}."
            )

        if field_name in seen_fields:
            # Duplicate sort field in user input
            continue

        seen_fields.add(field_name)
        col, attr_name = SORT_FIELD_MAP[field_name]
        sort_specs.append({
            "name": field_name,
            "column": col,
            "attr": attr_name,
            "direction": direction,
        })
        canonical_parts.append(f"-{field_name}" if direction == "desc" else field_name)

    # Inject 'id' tie-breaker if not explicitly sorted
    if "id" not in seen_fields:
        col, attr_name = SORT_FIELD_MAP["id"]
        # Default tie-breaker is ASC
        sort_specs.append({
            "name": "id",
            "column": col,
            "attr": attr_name,
            "direction": "asc",
        })
        canonical_parts.append("id")

    canonical_sort = ",".join(canonical_parts)
    return sort_specs, canonical_sort


def get_serializer(secret_key: str) -> URLSafeSerializer:
    return URLSafeSerializer(secret_key, salt="flask-bookstore-cursor-salt-v1")


def encode_cursor(
    last_item: Book,
    sort_specs: list[dict],
    genre: str | None,
    secret_key: str,
) -> str:
    """
    Encode the position of the last item into an opaque signed cursor.
    The payload includes column values, canonical sort string, and genre filter for integrity.
    """
    values = [getattr(last_item, spec["attr"]) for spec in sort_specs]
    canonical_sort = ",".join(
        f"-{s['name']}" if s["direction"] == "desc" else s["name"]
        for s in sort_specs
    )
    payload = {
        "v": values,
        "sort": canonical_sort,
        "genre": genre,
    }
    serializer = get_serializer(secret_key)
    return serializer.dumps(payload)


def decode_cursor(
    cursor_str: str,
    expected_sort: str,
    expected_genre: str | None,
    secret_key: str,
) -> list:
    """
    Decode and verify cursor signature and context binding.
    Returns the list of boundary values for keyset seeking.
    """
    serializer = get_serializer(secret_key)
    try:
        payload = serializer.loads(cursor_str)
    except (BadSignature, BadData, Exception):
        raise PaginationValidationError("Invalid cursor: signature verification failed or malformed token.")

    if not isinstance(payload, dict) or "v" not in payload or "sort" not in payload:
        raise PaginationValidationError("Invalid cursor: malformed payload structure.")

    # Context binding verification
    cursor_sort = payload.get("sort")
    if cursor_sort != expected_sort:
        raise PaginationValidationError(
            f"Invalid cursor: cursor sort configuration '{cursor_sort}' does not match request sort '{expected_sort}'."
        )

    cursor_genre = payload.get("genre")
    if cursor_genre != expected_genre:
        raise PaginationValidationError(
            f"Invalid cursor: cursor genre filter '{cursor_genre}' does not match request genre '{expected_genre}'."
        )

    return payload["v"]


def build_keyset_filter(sort_specs: list[dict], cursor_values: list):
    """
    Construct multi-key keyset condition:
    OR(
      col1 < v1,
      AND(col1 == v1, col2 > v2),
      AND(col1 == v1, col2 == v2, col3 > v3),
      ...
    )
    """
    if len(sort_specs) != len(cursor_values):
        raise PaginationValidationError("Invalid cursor: dimension mismatch with sort configuration.")

    branches = []
    for i, spec in enumerate(sort_specs):
        prefix_conditions = []
        for j in range(i):
            prev_spec = sort_specs[j]
            prev_val = cursor_values[j]
            prefix_conditions.append(prev_spec["column"] == prev_val)

        curr_col = spec["column"]
        curr_val = cursor_values[i]
        curr_dir = spec["direction"]

        if curr_dir == "asc":
            curr_cmp = curr_col > curr_val
        else:
            curr_cmp = curr_col < curr_val

        if prefix_conditions:
            branch = and_(*prefix_conditions, curr_cmp)
        else:
            branch = curr_cmp

        branches.append(branch)

    return or_(*branches)


def apply_order_by(query, sort_specs: list[dict]):
    order_clauses = [
        spec["column"].asc() if spec["direction"] == "asc" else spec["column"].desc()
        for spec in sort_specs
    ]
    return query.order_by(*order_clauses)


def execute_offset_pagination(query, offset: int, limit: int, sort_specs: list[dict]) -> dict:
    """
    Execute offset pagination:
    Applies sorting, counts total records, fetches page slice.
    """
    total = query.count()
    ordered_query = apply_order_by(query, sort_specs)
    items = ordered_query.offset(offset).limit(limit).all()
    has_next = (offset + limit < total)

    return {
        "items": items,
        "pagination": {
            "strategy": "offset",
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_next": has_next,
        },
    }


def execute_cursor_pagination(
    query,
    cursor: str | None,
    limit: int,
    sort_specs: list[dict],
    canonical_sort: str,
    genre: str | None,
    secret_key: str,
) -> dict:
    """
    Execute keyset/cursor pagination:
    Seeks via WHERE condition, queries limit + 1 items, signs next_cursor.
    """
    if cursor:
        cursor_values = decode_cursor(
            cursor_str=cursor,
            expected_sort=canonical_sort,
            expected_genre=genre,
            secret_key=secret_key,
        )
        keyset_filter = build_keyset_filter(sort_specs, cursor_values)
        query = query.filter(keyset_filter)

    ordered_query = apply_order_by(query, sort_specs)
    items = ordered_query.limit(limit + 1).all()

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more and page_items:
        last_item = page_items[-1]
        next_cursor = encode_cursor(last_item, sort_specs, genre, secret_key)

    return {
        "items": page_items,
        "page_info": {
            "next_cursor": next_cursor,
            "has_more": has_more,
        },
    }
