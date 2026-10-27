# BÁO CÁO BÀI KIỂM TRA THƯỜNG XUYÊN 2 (KT2)
## Học phần: Ứng dụng Trí tuệ Nhân tạo (AIA331) - ĐH CNTT&TT Thái Nguyên
**Đề tài:** Hệ thống Quản Lý Sân Thể Thao Rèn Luyện Thể Hình Trẻ ζɦàղɦ Cɦʊղɕ Có Tích Hợp AI  

---

### 1. Cấu trúc Dự án & Tổ chức Mã nguồn
Dự án được tổ chức chặt chẽ theo cấu trúc Module hóa:
- `app/routers/`: Tách biệt các API nghiệp vụ (`auth_router`, `pitch_router`, `booking_router`, `payment_router`, `maintenance_router`, `stats_router`, `ai_router`).
- `app/prompts/`: Quản lý các file System Prompt & User Prompt chuyên biệt.
- `app/services/`: Xử lý logic gọi AI Model và cơ chế dự phòng Fallback.
- `templates/` & `static/`: Giao diện Dashboard trực quan, hiển thị biểu đồ Chart.js.

### 2. Xác thực và Phân quyền (Authentication & Authorization)
- Sử dụng chuẩn mã hóa **bcrypt** (`passlib`) để hash mật khẩu an toàn.
- Cấp phát **JWT Bearer Token** với hạn dùng cấu hình trong `.env`.
- Triển khai FastAPI Dependency `require_roles([UserRole.ADMIN, UserRole.STAFF])` để bảo vệ các chức năng quan trọng (thêm/sửa sân, bảo trì, cấu hình giá).

### 3. Nghiệp vụ CRUD & Thuật toán Chống Trùng Lịch (Double-Booking Prevention)
- **Điều kiện giao thoa khung giờ:** Hai khung giờ $(S_1, E_1)$ và $(S_2, E_2)$ trên cùng 1 sân trong cùng 1 ngày bị trùng nhau khi:
  $$	ext{Overlap} = (S_1 < E_2) \land (E_1 > S_2)$$
- Khi phát hiện trùng lịch, API tự động chặn và phản hồi mã lỗi `409 Conflict` kèm thông báo chi tiết cho người dùng.

### 4. Nhật ký Minh chứng Sử dụng AI trong Lập trình
| Giai đoạn | Prompt AI Đã Sử Dụng | Kết quả AI Sinh Ra | Đánh giá & Hiệu Chỉnh Của Sinh Viên |
|---|---|---|---|
| Thiết kế CSDL | "Hãy thiết kế bảng cơ sở dữ liệu SQLAlchemy cho quản lý sân thể thao và đặt cọc" | Sinh các Model cơ bản | Bổ sung thêm trường `peak_price_per_hour` và enum `sport_type` |
| Thuật toán trùng lịch | "Viết hàm Python kiểm tra conflict giữa 2 khoảng thời gian đặt sân" | Sinh thuật toán logic giao thoa $(S_1 < E_2 \land E_1 > S_2)$ | Tích hợp vào query SQLAlchemy và xử lý exclude_booking_id khi cập nhật |
| Dashboard | "Tạo mã JavaScript vẽ biểu đồ Chart.js doanh thu 7 ngày" | Sinh cấu hình Chart.js | Tinh chỉnh màu sắc theo Tailwind Dark Mode và responsive |
