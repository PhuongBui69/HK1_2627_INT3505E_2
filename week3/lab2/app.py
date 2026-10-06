from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
import logging
import traceback
import uuid

app = Flask(__name__)

# Cấu hình logging để in ra console
logging.basicConfig(level=logging.ERROR)

ERROR_BASE = "https://api.example.com/probs"

# 1. Định nghĩa ApiProblem(Exception) dựa trên pattern mới
class ApiProblem(Exception):
    def __init__(self, status, title, detail=None, type_path=None, **extra):
        super().__init__()
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.extra = extra

# Hàm helper để build response chuẩn problem+json
def _problem(status, title, detail=None, type_path=None, **extra):
    body = {
        "type": f"{ERROR_BASE}/{type_path}" if type_path else "about:blank",
        "title": title,
        "status": status,
        "instance": request.path,
        "trace_id": str(uuid.uuid4()),
    }
    if detail:
        body["detail"] = detail
    
    # Cập nhật thêm các trường extra (ví dụ: resource_id)
    body.update(extra)

    resp = jsonify(body)
    resp.status_code = status
    resp.headers["Content-Type"] = "application/problem+json"
    return resp

# 2. Decorator @app.errorhandler cho ApiProblem
@app.errorhandler(ApiProblem)
def handle_api_problem(e):
    return _problem(
        status=e.status,
        title=e.title,
        detail=e.detail,
        type_path=e.type_path,
        **e.extra
    )

# 3. Handler fallback cho HTTPException (Ví dụ: 404 URL không tồn tại, 405)
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return _problem(
        status=e.code,
        title=e.name,
        detail=e.description
    )

# 4. Handler cho các exception chưa bắt (Unhandled exceptions -> 500)
@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    # Tránh bắt lại các lỗi đã bắt ở trên
    if isinstance(e, (ApiProblem, HTTPException)):
        raise e
        
    # Log chi tiết lỗi và stack trace ở server-side
    app.logger.error(f"Unhandled Exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    
    # Trả về lỗi 500 với message trung tính
    return _problem(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred on the server."
    )


# --- ROUTE KIỂM THỬ ---

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    # Giả lập database: chỉ có user id 42
    if id == 42:
        return jsonify({"id": 42, "name": "Admin User"}), 200
        
    # Nếu không tìm thấy, raise ApiProblem với extra field
    raise ApiProblem(
        status=404,
        title="User not found",
        type_path="user-not-found",
        resource_id=id
    )

# Route cố tình gây lỗi 500
@app.route('/resources/crash', methods=['GET'])
def crash():
    return str(1 / 0)

if __name__ == '__main__':
    # Slide ghi localhost:5000 nên mình có thể trả về port 5000 hoặc 5001 tùy bạn chạy
    app.run(debug=True, port=5000)
