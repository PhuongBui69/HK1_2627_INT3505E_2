"""
app.py: Ứng dụng Flask theo phong cách Design-First với Connexion.

Đặc điểm:
1. Thiết kế trước: File `openapi.yaml` định nghĩa đầy đủ paths, schemas và validation rules.
2. Định tuyến tự động: Connexion đọc trực tiếp file `openapi.yaml`, tự động bind các URL
   vào các hàm Python theo `operationId` (KHÔNG CẦN VIẾT SCRIPT THỦ CÔNG ĐỂ SINH ROUTE).
3. Tự động kiểm tra tính hợp lệ (validate): Connexion tự đối chiếu dữ liệu client gửi lên
   với schema trong file YAML (nếu thiếu field bắt buộc -> trả lỗi 400 tự động).
4. Phục vụ tài liệu Swagger UI tự động tại `/docs`.
"""

import sys
from pathlib import Path
import connexion
from connexion.options import SwaggerUIOptions
from connexion.resolver import RelativeResolver

SPEC_FILE = Path(__file__).parent / "openapi.yaml"

# 1. Khởi tạo Connexion Flask App với cấu hình Swagger UI
options = SwaggerUIOptions(swagger_ui_path="/docs")
app = connexion.FlaskApp(__name__, swagger_ui_options=options)

# 2. Bộ nhớ in-memory giả lập database
tasks_db = [
    {
        "id": 1,
        "title": "Thiết kế hợp đồng API bằng openapi.yaml",
        "description": "Viết đặc tả OpenAPI 3.0 trước khi code",
        "completed": True,
    },
    {
        "id": 2,
        "title": "Dùng Connexion tự động map routes",
        "description": "Không cần viết script thủ công để sinh code",
        "completed": True,
    },
    {
        "id": 3,
        "title": "Lập trình viên hoàn thiện business logic",
        "description": "Chỉ tập trung viết hàm xử lý nghiệp vụ",
        "completed": False,
    },
]


# 3. Business logic: Tên hàm khớp chính xác với `operationId` trong file openapi.yaml
def get_tasks():
    """Hàm xử lý cho GET /tasks (operationId: get_tasks)"""
    return tasks_db, 200


def create_task(body):
    """Hàm xử lý cho POST /tasks (operationId: create_task)
    Tham số `body` được Connexion tự động parse và validate theo schema trong openapi.yaml!
    Nếu client gửi thiếu trường `title`, Connexion sẽ tự động trả lỗi 400 Bad Request
    ngay trước khi hàm này được gọi.
    """
    new_task = {
        "id": len(tasks_db) + 1,
        "title": body["title"],
        "description": body.get("description", ""),
        "completed": body.get("completed", False),
    }
    tasks_db.append(new_task)
    return new_task, 201


# 4. Nạp file hợp đồng openapi.yaml vào Connexion
# RelativeResolver sẽ tự động tìm các hàm cùng tên với operationId trong module hiện tại
app.add_api(SPEC_FILE, resolver=RelativeResolver(sys.modules[__name__]))


if __name__ == "__main__":
    port = 5001
    print("=" * 60)
    print("  Tasks API (Design-First với Connexion) đang khởi chạy...")
    print(f"  - Server URL:   http://127.0.0.1:{port}")
    print(f"  - Swagger UI:   http://127.0.0.1:{port}/docs")
    print(f"  - OpenAPI Spec: http://127.0.0.1:{port}/openapi.json")
    print("=" * 60)
    app.run(port=port)
