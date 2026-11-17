# Lab 4 — Phân tích kết quả

Chạy ba kịch bản trên localhost với Flask và SQLite. Mỗi kịch bản bắt đầu từ database có 50 sách; user nghỉ 1–3 giây giữa các task. Số liệu lấy từ báo cáo HTML ngày 18/11/2026.

| Kịch bản | Users | Spawn rate | Thời gian | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2/s | 30s | 4 | 0.000% | 4.96 |
| B | 50 | 5/s | 60s | 4 | 0.215% | 23.34 |
| C | 200 | 50/s | 30s | 45 | 0.068% | 97.94 |

**1. Kịch bản nào có p95 cao nhất?**

C có p95 cao nhất, đạt 45 ms so với 4 ms của A và B. Khi tăng nhanh lên 200 user, server phải xử lý nhiều request đồng thời nên có thể phát sinh thêm thời gian chờ. POST `/books` chậm nhất trong C, với p95 là 58 ms. Việc ghi SQLite có thể góp phần gây chậm, nhưng chưa đo thời gian chờ database để kết luận chắc chắn.

**2. Endpoint nào có failure rate tăng theo số user?**

Chỉ GET `/books?year` ghi nhận lỗi: A có 0/20, B có 3/198 và C có 2/421 search thất bại. Đây đều là lỗi giả lập bằng `response.failure()`, còn HTTP thực tế vẫn là 200. Không ghi nhận lỗi HTTP thật trong cả ba kịch bản.

Failure rate không tăng đều theo số user: B cao hơn C do việc chèn lỗi là ngẫu nhiên. Xác suất 1% áp dụng riêng cho các request tìm theo năm, nên tỷ lệ lỗi trên toàn bộ request trong bảng thấp hơn 1%.

**3. Với SLO p95 < 300 ms, kịch bản nào đạt?**

Cả A, B và C đều đạt trong lần đo này. Có thể chọn B (50 user, 60 giây) làm baseline cho gate: p95 dưới 300 ms và không có lỗi HTTP thật; lỗi giả lập được thống kê riêng. C dùng để kiểm tra khi tải tăng nhanh.

Cần chạy lặp lại trước khi dùng làm gate ổn định. Kết quả trên máy local với database nhỏ chưa đủ để khẳng định hiệu năng production.

**4. Bonus: nếu connection pool giới hạn 5 thì sao?**

Khi cả 5 kết nối đều bận, request cần kết nối tiếp theo phải chờ, làm tăng độ trễ và có thể gây timeout. Tuy nhiên, 200 user không đồng nghĩa cả 200 đều đang truy vấn database cùng lúc.

Để kiểm chứng, đặt `pool_size=5`, `max_overflow=0`, chạy lại C rồi so sánh p95, RPS và log timeout với kết quả ban đầu. Lần đo hiện tại dùng pool size 5 và overflow 10, tức tối đa 15 kết nối. Chưa chạy thử cấu hình giới hạn cứng 5 kết nối.
