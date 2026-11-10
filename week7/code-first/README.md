# Code-First với Flask và flask-smorest

## 1. Khái niệm Code-First
Trong phong cách **Code-First**:
1. **Lập trình viên viết code trước**: Định nghĩa Schema dữ liệu và hàm xử lý API trực tiếp bằng Python (Flask + Marshmallow).
2. **Sinh tài liệu tự động (Không cần script)**: Khi server chạy, `flask-smorest` tự động phân tích code và phục vụ giao diện tài liệu Swagger UI cùng schema OpenAPI tại các endpoint `/docs` và `/openapi.json`.

---

## 2. Cấu trúc thư mục
```text
code-first/
├── app.py           # Ứng dụng Flask code-first (tự sinh docs tại runtime)
└── README.md        # Hướng dẫn chi tiết
```

---

## 3. Cách chạy

```bash
cd week7/code-first
python app.py
```

Server sẽ khởi chạy tại `http://127.0.0.1:5000`:
- **Swagger UI (Sinh tự động từ code tại runtime)**: [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
- **OpenAPI JSON Spec**: [http://127.0.0.1:5000/openapi.json](http://127.0.0.1:5000/openapi.json)

---


