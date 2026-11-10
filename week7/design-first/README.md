# Design-First với Connexion và Flask

## 1. Khái niệm Design-First
Trong phong cách **Design-First**:
1. **Thiết kế hợp đồng trước**: Dev viết tài liệu đặc tả chuẩn OpenAPI (`openapi.yaml`) định nghĩa toàn bộ endpoints, tham số, request body, responses và validation rules.
2. **Framework tự động map route (Không cần script thủ công)**: Framework **`connexion`** đọc trực tiếp file `openapi.yaml` và tự động ánh xạ (bind) các route tới các hàm Python theo `operationId`. Đồng thời, Connexion tự động validate request body theo schema trong YAML.
3. **Lập trình viên chỉ viết logic**: Dev chỉ cần viết các hàm Python tương ứng (`get_tasks`, `create_task`) để xử lý nghiệp vụ.

---

## 2. Cấu trúc thư mục
```text
design-first/
├── openapi.yaml     # Hợp đồng API chuẩn OpenAPI 3.0 (viết trước)
├── app.py           # Connexion nạp openapi.yaml và chứa business logic
└── README.md        # Hướng dẫn chi tiết
```

---

## 3. Cách chạy

```bash
cd week7/design-first
python app.py
```

Ứng dụng sẽ chạy tại `http://127.0.0.1:5001`:
- **Swagger UI (Connexion phục vụ trực tiếp từ openapi.yaml)**: [http://127.0.0.1:5001/docs](http://127.0.0.1:5001/docs)
- **OpenAPI Schema (JSON)**: [http://127.0.0.1:5001/openapi.json](http://127.0.0.1:5001/openapi.json)

---



