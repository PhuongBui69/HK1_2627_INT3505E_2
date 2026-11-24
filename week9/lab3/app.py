import os
from datetime import datetime

from flask import Flask

from sunset import deprecate_at

app = Flask(__name__)
V1_SUNSET = datetime.fromisoformat(
    os.getenv("V1_SUNSET", "2026-12-31T23:59:59+00:00")
)


@app.get("/api/v1/users/<int:uid>")
@deprecate_at(V1_SUNSET, replacement="/api/v2/users")
def get_v1(uid):
    return {"id": uid, "full_name": "Nguyễn Văn A"}
