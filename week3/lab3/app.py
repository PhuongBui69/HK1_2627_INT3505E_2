from flask import Flask, request, jsonify
import base64
import json

app = Flask(__name__)

# Demo data
orders = [
    {
        "id": i,
        "customer_id": 1000 + (i % 5),
        "status": ["pending", "paid", "cancelled"][i % 3],
        "total": i * 100,
    }
    for i in range(1, 31)
]

ALLOWED_FIELDS = {"id", "customer_id", "status", "total"}
ALLOWED_SORT_FIELDS = {"id", "customer_id", "total"}


def encode_cursor(last_order, sort_field):
    """
    Cursor chứa thông tin vị trí cuối cùng đã đọc.
    Client không cần biết bên trong cursor có gì.
    """
    data = {
        "sort": sort_field,
        "last_value": last_order[sort_field],
        "last_id": last_order["id"]
    }

    raw = json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor):
    """
    Decode cursor.
    Cursor sai / hỏng -> ValueError.
    """
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        return json.loads(raw)
    except Exception:
        raise ValueError("Invalid cursor")


@app.get("/orders")
def get_orders():

    # ============================================================
    # 1. LIMIT
    # ============================================================

    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        return jsonify({
            "error": "limit must be an integer"
        }), 400

    if limit <= 0:
        return jsonify({
            "error": "limit must be greater than 0"
        }), 400

    if limit > 20:
        return jsonify({
            "error": "limit must be <= 20"
        }), 400

    # ============================================================
    # 2. FILTER
    # ============================================================

    result = orders

    status = request.args.get("status")
    if status:
        result = [
            order
            for order in result
            if order["status"] == status
        ]

    customer_id = request.args.get("customer_id")

    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return jsonify({
                "error": "customer_id must be integer"
            }), 400

        result = [
            order
            for order in result
            if order["customer_id"] == customer_id
        ]

    # ============================================================
    # 3. SORT
    # ============================================================

    sort = request.args.get("sort", "id")

    descending = sort.startswith("-")

    if descending:
        sort_field = sort[1:]
    else:
        sort_field = sort

    if sort_field not in ALLOWED_SORT_FIELDS:
        return jsonify({
            "error": "invalid sort field"
        }), 400

    # Sort + id để thứ tự deterministic
    result = sorted(
        result,
        key=lambda x: (x[sort_field], x["id"]),
        reverse=descending
    )

    # ============================================================
    # 4. CURSOR
    # ============================================================

    if "cursor" in request.args:

        cursor = request.args.get("cursor")

        # Lab yêu cầu cursor hỏng -> 400
        if not cursor:
            return jsonify({
                "error": "cursor cannot be empty"
            }), 400

        try:
            cursor_data = decode_cursor(cursor)
        except ValueError:
            return jsonify({
                "error": "invalid cursor"
            }), 400

        # Cursor phải cùng sort với request hiện tại
        if cursor_data["sort"] != sort_field:
            return jsonify({
                "error": "cursor does not match sort"
            }), 400

        last_value = cursor_data["last_value"]
        last_id = cursor_data["last_id"]

        # ========================================================
        # KEYSET / SEEK
        #
        # Nếu ASC:
        #   lấy record sau (last_value, last_id)
        #
        # Nếu DESC:
        #   lấy record trước (last_value, last_id)
        # ========================================================

        if not descending:
            result = [
                order
                for order in result
                if (
                    order[sort_field] > last_value
                    or (
                        order[sort_field] == last_value
                        and order["id"] > last_id
                    )
                )
            ]
        else:
            result = [
                order
                for order in result
                if (
                    order[sort_field] < last_value
                    or (
                        order[sort_field] == last_value
                        and order["id"] < last_id
                    )
                )
            ]

    # ============================================================
    # 5. LẤY limit + 1
    #
    # Lấy thêm 1 record để biết còn trang tiếp theo hay không.
    # ============================================================

    page = result[:limit + 1]

    has_next = len(page) > limit

    page = page[:limit]

    # ============================================================
    # 6. NEXT CURSOR
    # ============================================================

    next_cursor = None

    if has_next and page:
        next_cursor = encode_cursor(
            page[-1],
            sort_field
        )

    # ============================================================
    # 7. SPARSE FIELDSETS
    # ============================================================

    fields = request.args.get("fields")

    if fields:

        requested_fields = [
            field.strip()
            for field in fields.split(",")
        ]

        # Field không tồn tại -> 400
        for field in requested_fields:
            if field not in ALLOWED_FIELDS:
                return jsonify({
                    "error": f"unknown field: {field}"
                }), 400

        page = [
            {
                field: order[field]
                for field in requested_fields
            }
            for order in page
        ]

    # ============================================================
    # 8. RESPONSE
    # ============================================================

    return jsonify({
        "data": page,
        "pagination": {
            "limit": limit,
            "has_next": has_next,
            "next_cursor": next_cursor
        }
    })


if __name__ == "__main__":
    app.run(
        host="localhost",
        port=5000,
        debug=True
    )