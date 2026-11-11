from flask import jsonify
from werkzeug.exceptions import HTTPException

from .business import BusinessError, ConflictError, NotFoundError


def register_error_handlers(app):
    @app.errorhandler(BusinessError)
    def business_error(error):
        status = 400
        if isinstance(error, NotFoundError):
            status = 404
        elif isinstance(error, ConflictError):
            status = 409
        return jsonify(error=error.code, detail=str(error)), status

    @app.errorhandler(HTTPException)
    def http_error(error):
        status = error.code
        data = getattr(error, "data", {}) or {}
        detail = data.get("errors") or data.get("message") or error.description
        # Lab quy ước JSON sai cú pháp/content-type là 400.
        if status == 415:
            status = 400
        name = "bad_request" if status == 400 else error.name.lower().replace(" ", "_")
        response = error.get_response()
        response.data = app.json.dumps({"error": name, "detail": detail})
        response.content_type = "application/json"
        response.status_code = status
        return response

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Unhandled request error")
        return jsonify(error="internal_error", detail="Lỗi máy chủ."), 500
