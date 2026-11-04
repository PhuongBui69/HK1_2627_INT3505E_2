# Security Audit - Social Network API

Phạm vi: `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}`.

## Các điểm có thể lộ lọt hoặc bị khai thác

| # | Điểm rủi ro | Tác động | Biện pháp giảm thiểu |
|---|---|---|---|
| 1 | **Password bị ghi vào log hoặc lưu plaintext** tại login, reverse proxy hoặc database. | Lộ credential có thể dẫn tới chiếm tài khoản. | Chỉ lưu password hash bằng Argon2id (hoặc bcrypt phù hợp); không log request body/Authorization; thông báo lỗi đăng nhập chung; triển khai rate limit trên phànn login |
| 2 | **Access token bị lộ ở client hoặc log** (localStorage, console, URL, crash report, proxy log). | Kẻ khác có thể dùng token như bearer credential cho tới khi token hết hạn/ bị thu hồi. | Không truyền token qua query string; redact `Authorization`; không log token; với web cân nhắc BFF + cookie `HttpOnly`, `Secure`, `SameSite` phù hợp và có CSRF defense; nếu dùng bearer ở SPA thì hạn chế thời gian lưu và bề mặt XSS. |
| 3 | **Refresh token bị đánh cắp hoặc replay** do thời hạn dài và không rotate. | Attacker có thể liên tục xin access token mới sau khi access token ban đầu hết hạn. | Refresh rotation single-use; lưu hash/reference của `jti` hoặc token family ở server; phát hiện reuse và revoke cả family/session; refresh chỉ được dùng tại `/auth/refresh`. |
| 4 | **JWT verification yếu**: chấp nhận `alg` từ token, `alg=none`, algorithm confusion HS/RS, bỏ qua `iss`, `aud`, `exp` hoặc phân biệt sai access/refresh. | Token giả hoặc token dành cho dịch vụ khác có thể được chấp nhận. | Dùng thư viện được duy trì; allowlist thuật toán theo cấu hình tin cậy; tách khóa theo thuật toán; kiểm tra chữ ký, `iss`, `aud`, `exp`, `nbf` khi có, `token_use` và trạng thái revoke. Không tự viết crypto. |
| 5 | **BOLA tại `GET /posts/{id}`**: chỉ kiểm tra token/scope mà không kiểm tra visibility/quan hệ với post. | User A có thể đọc post riêng tư của User B bằng cách đổi ID. | Sau AuthN và scope `posts:read`, kiểm tra object-level policy: public/friends/private, tác giả, quan hệ bạn bè đã chấp nhận và trạng thái block. Không tin `owner_id` từ client. Trả 404 nhất quán cho post không tồn tại hoặc không được xem. |
| 6 | **Scope bị cấp quá rộng hoặc không được kiểm tra ở từng endpoint.** | Token hợp lệ có thể thực hiện hành động ngoài nhu cầu của client. | Cấp quyền tối thiểu; `GET /posts/{id}` yêu cầu `posts:read`; kiểm tra scope theo từng request và mặc định deny. Scope không thay thế ownership/visibility. |
| 7 | **Login bị brute-force / credential stuffing** hoặc response phân biệt email không tồn tại với password sai. | Chiếm tài khoản, dò tài khoản hợp lệ hoặc gây quá tải. | Rate-limit theo IP và định danh tài khoản theo cách tránh lockout gây DoS; trả vè phản hồi `401 invalid_credentials` chung chung; giám sát bất thường và thêm backoff phù hợp. |
| 8 | **Lộ dữ liệu nhạy cảm trong response hoặc mass assignment.** | Có thể lộ `password_hash`, email/PII không cần thiết hoặc cho phép client sửa field nội bộ. | Trả DTO/allowlist field; không serialize raw DB row; `LoginRequest` từ chối field thừa; không đưa password, secret hoặc PII không cần thiết vào JWT claims. |
| 9 | **Secret ký JWT / cấu hình bị commit vào Git hoặc dùng chung giữa môi trường.** | Người lấy được secret có thể ký token giả; ảnh hưởng có thể kéo dài tới lúc key bị thay và token cũ hết hiệu lực. | Dùng secret manager hoặc biến môi trường; secret ngẫu nhiên đủ mạnh (HS256 tối thiểu 256 bit); không commit `.env`; có quy trình rotate/revoke key.|
| 10 | **Truyền token/password không qua TLS hoặc CORS quá rộng.** | Credential có thể bị nghe lén hoặc website không tin cậy có thể gọi API từ browser trong cấu hình sai. | Chỉ phục vụ HTTPS; bật HSTS ở production; giới hạn CORS theo origin cần thiết; không kết hợp wildcard origin với credentialed requests. Nếu dùng cookie, bổ sung CSRF protection. |

## Quy tắc xác thực và phân quyền theo endpoint

| Endpoint | Authentication | Scope | Kiểm tra bổ sung |
|---|---|---|---|
| `POST /auth/login` | Public | Không yêu cầu scope | Verify password hash; generic login error; rate-limit. |
| `POST /auth/refresh` | Refresh JWT riêng | Không yêu cầu business scope | `token_use=refresh`; kiểm tra session/revocation; rotate một lần; từ chối access token. |
| `GET /posts/{id}` | Access JWT | `posts:read` | Object-level authorization theo visibility, owner/friend và block relationship để chống BOLA. |
