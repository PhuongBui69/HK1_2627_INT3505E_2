# Lab 1 BTVN - Product & Order API

Project thực hành buổi 7: Flask-smorest (code-first), Marshmallow, SQLAlchemy 2.x,
Flask-Migrate và Gunicorn. Chạy local bằng SQLite, Docker Compose bằng PostgreSQL.

## Tổ chức code

```text
src/product_api/
├── factory.py       # create_app(), khởi tạo extension và đăng ký blueprint
├── config.py        # cấu hình từ biến môi trường
├── extensions.py    # db, migrate dùng chung
├── api/             # controller: blueprint, HTTP status, request hooks
├── schemas/         # DTO: validate input và serialize output, chia theo resource
├── services/        # application: nghiệp vụ sản phẩm, đơn hàng, health check
├── persistence/
│   ├── models/      # entity SQLAlchemy: product.py, order.py, order_item.py
│   ├── repositories/ # SELECT/UPDATE, phân trang, eager loading; không commit
│   └── transaction.py # commit/rollback, chuyển lỗi constraint DB
└── exceptions/
    ├── business.py  # lỗi nghiệp vụ, không phụ thuộc HTTP
    └── handlers.py  # global handler: ánh xạ exception sang JSON + HTTP status
migrations/          # migration Alembic đã có sẵn
tests/               # pytest với SQLite in-memory độc lập cho từng test
```

Luồng xử lý tương tự layered architecture trong Spring:
`Request -> API + Schema -> Service -> Repository -> Model/DB`.
API chỉ gọi service, không truy vấn DB hay sửa entity. Service xử lý nghiệp vụ và
quyết định transaction; repository tập trung truy cập dữ liệu. Model chỉ mô tả bảng
và quan hệ; schema không gọi DB. Exception handler chỉ chuyển lỗi thành response,
rollback nằm trong transaction để cả khi gọi service ngoài HTTP cũng hoạt động đúng.
Các tầng dùng hàm/module Python trực tiếp, chưa cần interface hay DI container.

Quan hệ: `Order (1) -> (N) OrderItem (N) -> (1) Product`.
Một đơn có nhiều sản phẩm; `Order` không giữ trực tiếp một `product_id`.
`OrderItem` được tạo và trả về trong blueprint riêng `/api/v1/orders`.

## Chạy bằng Docker

Cần Docker và Docker Compose, chạy trong thư mục `week7/lab1-btvn`:

```bash
docker compose up --build -d --wait
docker compose logs -f api
```

API: `http://localhost:5000`. Swagger UI: `http://localhost:5000/docs`.
OpenAPI JSON: `http://localhost:5000/openapi.json`.
Swagger UI tải thư viện từ CDN nên cần Internet để hiển thị giao diện.

Compose tự đợi PostgreSQL sẵn sàng, chạy `flask db upgrade`, rồi khởi động Gunicorn.
Không cần tạo `.env` hay sửa cấu hình. Thông tin DB trong Compose chỉ dùng cho bài lab.
Volume `pgdata` giữ dữ liệu khi dừng bằng `docker compose down`.

## Chạy local và test

Cần Python 3.12 trở lên. Cũng chạy trong thư mục `week7/lab1-btvn`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install --no-deps -e .
flask --app wsgi:app db upgrade
flask --app wsgi:app run --debug
```

Mặc định DB là `instance/lab1.db`. Muốn đổi DB, export `DB_URL` trước khi chạy;
các biến hỗ trợ được liệt kê trong `.env.example` (không tự đọc file `.env`).
Khi sửa model: `flask --app wsgi:app db migrate -m "mo ta"`, đọc revision rồi
chạy `flask --app wsgi:app db upgrade`.

```bash
python -m pytest -q
```

Test bao gồm POST, CRUD, validation, phân trang, SKU trùng, soft delete, reserve,
rollback đơn hàng (cả khi gọi service trực tiếp) và health check khi DB lỗi.
Test GET orders dùng session mới,
đếm **4 SELECT** (COUNT, orders, items, products) cho cả 1 và 5 đơn để phát hiện N+1;
GET chi tiết dùng **3 SELECT**. Eager loading dùng `selectinload` cho items và products.
Với dữ liệu lớn, SQLAlchemy có thể chia thêm batch.

## API

| Method | Đường dẫn | Chức năng |
| --- | --- | --- |
| GET | `/api/v1/products?page=1&size=20` | Danh sách, phân trang |
| POST | `/api/v1/products` | Tạo sản phẩm, trả 201 |
| GET | `/api/v1/products/<id>` | Chi tiết sản phẩm |
| PATCH | `/api/v1/products/<id>` | Chỉ sửa field có trong body |
| DELETE | `/api/v1/products/<id>` | Soft delete, trả 204 |
| POST | `/api/v1/products/<id>/reserve` | Body `{"qty": 1}`, giảm tồn kho |
| POST | `/api/v1/orders` | Tạo đơn với nhiều OrderItem, trả 201 |
| GET | `/api/v1/orders?page=1&size=20` | Danh sách đơn kèm items và products |
| GET | `/api/v1/orders/<id>` | Chi tiết đơn kèm items và products |
| GET | `/healthz` | Liveness: không truy cập DB |
| GET | `/ready` | Readiness: `SELECT 1`, trả 503 nếu DB lỗi |

Phân trang trả `{"items": [...], "page": 1, "size": 20, "total": N}`;
`page >= 1`, `1 <= size <= 100`. SKU dài 3-32, name dài 1-255, giá và tồn kho
không âm; tồn kho mặc định 0. Sản phẩm archived bị ẩn khỏi list/get và không thể sửa,
reserve hay thêm vào đơn mới. SKU vẫn duy nhất kể cả sản phẩm đã soft delete.
Lỗi trả `{"error": "...", "detail": ...}` với 400 (JSON/content-type), 404, 409 hoặc 422.

Ví dụ trên DB mới:

```bash
curl -X POST http://localhost:5000/api/v1/products \
  -H 'Content-Type: application/json' \
  -d '{"sku":"BOOK-01","name":"Sach SOA","price_cents":15000,"qty_in_stock":10}'

curl -X POST http://localhost:5000/api/v1/products \
  -H 'Content-Type: application/json' \
  -d '{"sku":"PEN-01","name":"But","price_cents":2000,"qty_in_stock":20}'

curl -X POST http://localhost:5000/api/v1/orders \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":1,"qty":2},{"product_id":2,"qty":3}]}'

curl http://localhost:5000/api/v1/orders
```

Tạo đơn tự trừ tồn kho và lưu `unit_price_cents` tại thời điểm mua; không cần gọi
`reserve` trước. Mỗi sản phẩm xuất hiện một lần trong đơn, tăng `qty` nếu mua nhiều.
Thiếu hàng trả 409 và rollback toàn bộ đơn cùng tồn kho. Giá đã lưu và liên kết
OrderItem được giữ lại khi giá sản phẩm thay đổi hoặc sản phẩm bị soft delete.
Phạm vi bài lab không có thanh toán, tài khoản hay quản lý trạng thái đơn hàng.
