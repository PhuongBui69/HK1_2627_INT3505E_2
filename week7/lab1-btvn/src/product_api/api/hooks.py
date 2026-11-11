from flask import abort, request


def register_request_hooks(app):
    @app.before_request
    def require_json():
        if request.blueprint in {"products", "orders"} and request.method in {"POST", "PATCH"}:
            if not request.is_json:
                abort(400, description="Request phải có Content-Type: application/json.")
