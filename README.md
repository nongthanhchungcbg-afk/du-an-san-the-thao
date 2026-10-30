# 🏆 Hệ thống Quản Lý Sân Thể Thao Rèn Luyện Thể Hình Trẻ ζɦàղɦ Cɦʊղɕ (Tích Hợp AI)
> **Đề tài Học phần: Ứng dụng Trí tuệ Nhân tạo - AIA331 (ICTU)**  
> **Mã số đề tài:** 80302  

---

## 🚀 Hướng dẫn Chạy Dự Án Trên Visual Studio Code

### Cách 1: Chạy nhanh bằng file `run.bat` (Khuyên dùng trên Windows)
1. Mở thư mục `F:\Du_An_San_The_Thao` trong Visual Studio Code hoặc File Explorer.
2. Nhấp đúp chuột vào file **`run.bat`**.
3. Hệ thống sẽ tự động cài thư viện, nạp dữ liệu mẫu và mở server tại:  
   👉 **Trang chủ Web Dashboard:** `http://127.0.0.1:8000`  
   👉 **Tài liệu API Swagger:** `http://127.0.0.1:8000/docs`

---

### Cách 2: Chạy thủ công qua Terminal của VS Code
1. Mở Terminal trong VS Code (`Ctrl + ~`)
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Khởi tạo cơ sở dữ liệu mẫu:
   ```bash
   python -m app.seed_data
   ```
4. Khởi động Web Server FastAPI:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Mở trình duyệt và truy cập: `http://127.0.0.1:8000`

---

## 🔑 Tài Khoản Đăng Nhập Mẫu (Có nút đăng nhập nhanh 1 chạm trên giao diện)
| Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn |
|---|---|---|---|
| **Admin (Quản lý)** | `nongthanhchung` | `Admin` | Toàn quyền quản trị sân, bảng giá, xem báo cáo AI |
| **Nhân viên (Lễ tân)** | `nguyenvanloc` | `Nhanvien` | Đặt sân, hủy/đổi lịch, thu cọc, sinh tin nhắn AI |
| **Khách hàng** | `hoangtrituong` | `Khachhang` | Tìm sân, xem bảng giá, nhờ AI tư vấn giờ trống |

---

## 🤖 3 Chức Năng Trí Tuệ Nhân Tạo (AI) Nổi Bật
1. **AI Gợi ý khung giờ còn trống:** Phân tích nhu cầu tự nhiên của khách và đối chiếu chính xác với các slot trống thực tế trong CSDL SQLite.
2. **AI Tự động sinh thông báo:** Tạo mẫu SMS ngắn gọn, Zalo OA thân thiện và Email trang trọng gửi cho khách đặt sân.
3. **AI Tóm tắt công suất & Chiến lược khuyến mãi:** Phân tích tỷ lệ lấp đầy giờ cao điểm/thấp điểm và đề xuất voucher kích cầu tự động.

---

## 🧪 Chạy Kiểm Thử Tự Động (Automated Tests)
Để kiểm tra tính năng chống trùng lịch và AI service, chạy lệnh:
```bash
pytest
```
