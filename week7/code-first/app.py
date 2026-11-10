from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields

# ==============================================================================
# PHONG CÁCH CODE-FIRST VỚI FLASK-SMOREST
#
# Đặc điểm:
# 1. Viết code trước: Lập trình viên định nghĩa Schema dữ liệu và các route bằng Python.
# 2. Sinh tài liệu tự động: flask-smorest tự động sinh đặc tả OpenAPI 3.0 và Swagger UI
#    tại runtime từ chính các decorator và Schema trong code (KHÔNG CẦN VIẾT SCRIPT THỦ CÔNG).
# ==============================================================================

app = Flask(__name__)

# Cấu hình Swagger / OpenAPI Documentation
app.config["API_TITLE"] = "Tasks API (Code-First)"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)


# 1. Định nghĩa Data Schemas bằng Marshmallow
class TaskSchema(Schema):
    """Schema dữ liệu của một Task trả về cho client"""
    id = fields.Int(dump_only=True, metadata={"description": "ID tự tăng của task"})
    title = fields.String(required=True, metadata={"description": "Tiêu đề công việc"})
    description = fields.String(load_default="", metadata={"description": "Mô tả chi tiết"})
    completed = fields.Boolean(load_default=False, metadata={"description": "Trạng thái hoàn thành"})


class TaskCreateSchema(Schema):
    """Schema dữ liệu khi client gửi request tạo mới một Task"""
    title = fields.String(required=True, metadata={"description": "Tiêu đề công việc"})
    description = fields.String(load_default="", metadata={"description": "Mô tả chi tiết"})
    completed = fields.Boolean(load_default=False, metadata={"description": "Trạng thái hoàn thành"})


# 2. Dữ liệu in-memory đơn giản phục vụ demo
tasks_db = [
    {
        "id": 1,
        "title": "Nghiên cứu phong cách Code-First",
        "description": "Dùng flask-smorest để tự động sinh OpenAPI document từ code tại runtime",
        "completed": True,
    },
    {
        "id": 2,
        "title": "Nghiên cứu phong cách Design-First",
        "description": "Viết file openapi.yaml trước rồi dùng Connexion tự map route",
        "completed": False,
    },
]


# 3. Tạo Blueprint chứa các API liên quan đến Task
blp = Blueprint("tasks", "tasks", url_prefix="/tasks", description="Các API quản lý công việc (Tasks)")


@blp.route("", strict_slashes=False)
class TaskList(MethodView):
    @blp.response(200, TaskSchema(many=True))
    def get(self):
        """API 1: Lấy danh sách tasks
        Tự động tạo mô tả response schema trong tài liệu Swagger.
        """
        return tasks_db

    @blp.arguments(TaskCreateSchema)
    @blp.response(201, TaskSchema)
    def post(self, new_data):
        """API 2: Tạo mới một task
        Tự động kiểm tra tính hợp lệ của request body (validate) và sinh tài liệu Swagger.
        """
        new_task = {
            "id": len(tasks_db) + 1,
            "title": new_data["title"],
            "description": new_data.get("description", ""),
            "completed": new_data.get("completed", False),
        }
        tasks_db.append(new_task)
        return new_task


# Đăng ký Blueprint vào API
api.register_blueprint(blp)


if __name__ == "__main__":
    print("=" * 60)
    print("  Tasks API (Code-First) đang khởi chạy...")
    print("  - Server URL:   http://127.0.0.1:5000")
    print("  - Swagger UI:   http://127.0.0.1:5000/docs")
    print("  - OpenAPI JSON: http://127.0.0.1:5000/openapi.json")
    print("=" * 60)
    app.run(port=5000, debug=True)
