# BÁO CÁO BÀI KIỂM TRA THƯỜNG XUYÊN 1 (KT1)
## Học phần: Ứng dụng Trí tuệ Nhân tạo (AIA331) - ĐH CNTT&TT Thái Nguyên
**Đề tài:** Hệ thống Quản Lý Sân Thể Thao Rèn Luyện Thể Hình Trẻ ζɦàղɦ Cɦʊղɕ Có Tích Hợp AI  
**Mã đề tài:** 80302  

---

### 1. Phân tích bài toán quản lý & Bối cảnh
- **Bối cảnh thực tế:** Các cơ sở kinh doanh sân bóng đá mini, sân cầu lông, tennis thường gặp khó khăn khi tiếp nhận đặt lịch qua điện thoại hoặc ghi sổ tay: dễ dẫn đến tình trạng **trùng lịch (double-booking)**, khó nắm bắt công suất giờ cao điểm và bỏ phí các khung giờ thấp điểm ban ngày.
- **Giải pháp:** Xây dựng hệ thống web quản lý đặt sân tự động hóa toàn diện, đồng thời tích hợp **AI Engine (Google Gemini & Rule Engine)** để:
  1. Tư vấn và gợi ý khung giờ còn trống chính xác từ cơ sở dữ liệu.
  2. Tự động sinh tin nhắn xác nhận, nhắc lịch cho khách hàng.
  3. Báo cáo tổng hợp công suất và đề xuất voucher giờ thấp điểm.

### 2. Các Actor và Use Case chính
- **Actor 1: Admin (Quản trị viên)**
  - Quản lý sân, loại sân, cấu hình bảng giá giờ thường / cao điểm.
  - Quản lý tài khoản nhân viên, xem báo cáo doanh thu & công suất AI.
- **Actor 2: Staff (Nhân viên / Lễ tân)**
  - Tiếp nhận đặt sân, đổi lịch, hủy lịch cho khách.
  - Ghi nhận thanh toán, tiền đặt cọc.
  - Lên lịch bảo trì sân kỹ thuật.
  - Sử dụng AI để gửi tin nhắn xác nhận/nhắc lịch thi đấu cho khách.
- **Actor 3: Customer (Khách hàng / Người chơi)**
  - Xem danh sách sân, bảng giá, trạng thái sân.
  - Tìm kiếm khung giờ trống với sự trợ giúp của AI.
  - Đặt sân trực tuyến và theo dõi lịch sử đặt.

### 3. Thiết kế Cơ sở dữ liệu (ERD Relational Schema)
- **Bảng `users`**: `id (PK)`, `username (UQ)`, `email (UQ)`, `hashed_password`, `full_name`, `phone`, `role (ADMIN/STAFF/CUSTOMER)`, `is_active`, `created_at`.
- **Bảng `pitches`**: `id (PK)`, `name`, `sport_type (FOOTBALL/BADMINTON/TENNIS)`, `price_per_hour`, `peak_price_per_hour`, `status (AVAILABLE/MAINTENANCE/INACTIVE)`, `description`, `image_url`.
- **Bảng `bookings`**: `id (PK)`, `user_id (FK)`, `pitch_id (FK)`, `customer_name`, `customer_phone`, `booking_date`, `start_time`, `end_time`, `total_price`, `deposit_amount`, `status (CONFIRMED/CANCELLED/COMPLETED)`, `note`.
- **Bảng `payments`**: `id (PK)`, `booking_id (FK)`, `amount`, `payment_type (DEPOSIT/FULL_PAYMENT)`, `payment_method (CASH/BANK_TRANSFER/MOMO)`, `status`, `created_at`.
- **Bảng `maintenances`**: `id (PK)`, `pitch_id (FK)`, `start_date`, `end_date`, `reason`, `cost`, `status`.

### 4. Kiến trúc Hệ thống & Vị trí Ứng dụng AI
- **Frontend:** Single Page Application (HTML5, TailwindCSS, FontAwesome, Chart.js).
- **Backend:** Python FastAPI RESTful API, SQLAlchemy ORM.
- **AI Integration Layer:** `app/services/ai_service.py` kết nối với `app/prompts/` (System Prompt & User Prompt) gọi Google Gemini 1.5 Flash hoặc Heuristic Fallback Engine.
