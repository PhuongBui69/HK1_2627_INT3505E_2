- Request tới /resources/{id} trả 404, body có type/title/detail/status/instance, không lộ stack trace.
![alt text](image/image-1.png)

- Thiếu header Accept, vẫn trả problem+json cho lỗi API.
![alt text](image/image.png)

-Truyền header Accept báo chỉ nhận application/json, vẫn trả problem+json cho lỗi API.
![alt text](image/image-2.png)

- Gặp exception chưa bắt, trả 500 với message tính và log server-side
![alt text](image/image-3.png)