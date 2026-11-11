from flask import Blueprint

from ..services.health import check_readiness

blp = Blueprint("health", __name__)


@blp.get("/healthz")
def liveness():
    # Chỉ kiểm tra process Flask, không truy vấn DB.
    return {"status": "ok"}


@blp.get("/ready")
def readiness():
    result = check_readiness()
    return result, 200 if result["status"] == "ok" else 503
