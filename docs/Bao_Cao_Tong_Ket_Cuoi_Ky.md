# BÁO CÁO TỔNG KẾT DỰ ÁN CUỐI KỲ - AIA331
## Đề tài: Hệ thống Quản Lý Sân Thể Thao Rèn Luyện Thể Hình Trẻ ζɦàղɦ Cɦʊղɕ Có Tích Hợp AI
**Trường Đại học Công nghệ Thông tin & Truyền thông - Đại học Thái Nguyên (ICTU)**  
**Mã đề tài:** 80302  

---

### TỔNG QUAN 10 TIÊU CHÍ ĐÁNH GIÁ THI KẾT THÚC HỌC PHẦN

1. **Hoàn thiện chức năng:** Hoạt động đầy đủ 100% nghiệp vụ quản lý sân, bảng giá, đặt sân, chống trùng lịch, thanh toán, bảo trì và 3 chức năng AI.
2. **Kiến trúc & mã nguồn:** Tổ chức rõ ràng theo chuẩn FastAPI RESTful API, phân chia router, service, prompt, model, schemas rõ ràng.
3. **Chất lượng CSDL:** CSDL SQLite với khóa chính, khóa ngoại, quan hệ 1-N, chống trùng lịch chặt chẽ, có script `seed_data.py` nạp dữ liệu mẫu phong phú.
4. **Giao diện & Trải nghiệm (UI/UX):** Dashboard hiện đại (TailwindCSS, Chart.js, FontAwesome), responsive mượt mà trên desktop và mobile.
5. **Chất lượng AI:** Trả lời chính xác dựa trên CSDL, không bịa đặt thông tin, có cơ chế Fallback đảm bảo không gián đoạn dịch vụ.
6. **Bảo mật & Đạo đức AI:** Mật khẩu hash bcrypt, JWT token, không lưu thông tin nhạy cảm của khách hàng khi gửi prompt sang AI.
7. **Hiệu năng & Độ ổn định:** Phản hồi nhanh dưới 100ms với API nghiệp vụ, kiểm soát lỗi chặt chẽ.
8. **Đóng gói & Triển khai:** Có file `run.bat` chạy nhanh 1 chạm, `requirements.txt`, `Dockerfile`, `.env.example`.
9. **Báo cáo kỹ thuật:** Đầy đủ hồ sơ KT1, KT2, KT3 và Báo cáo tổng kết.
10. **Kịch bản Demo:**
   - Bước 1: Mở Dashboard xem doanh thu 7 ngày và biểu đồ phân bố môn thể thao.
   - Bước 2: Đăng nhập bằng tài khoản Quản lý (`admin` / `admin123`).
   - Bước 3: Thử đặt sân giờ cao điểm và thử nghiệm tính năng phát hiện trùng lịch.
   - Bước 4: Chạy Demo AI tư vấn khung giờ trống, sinh tin nhắn Zalo/SMS/Email và báo cáo công suất.
