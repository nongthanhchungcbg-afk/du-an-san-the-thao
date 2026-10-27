# BÁO CÁO BÀI KIỂM TRA THƯỜNG XUYÊN 3 (KT3)
## Học phần: Ứng dụng Trí tuệ Nhân tạo (AIA331) - ĐH CNTT&TT Thái Nguyên
**Đề tài:** Đánh Giá & Tối Ưu Hóa Chức Năng AI Trong Hệ Thống Quản Lý Sân Thể Thao  

---

### 1. Tách biệt Thiết kế Prompt
Dự án tách biệt hoàn toàn nội dung prompt khỏi logic mã nguồn nghiệp vụ:
- `app/prompts/slot_suggestion.py`: System Prompt định hình vai trò trợ lý tư vấn + User Prompt nạp ngữ cảnh dữ liệu thực tế từ CSDL.
- `app/prompts/notification_gen.py`: Chuyên môn hóa sinh 3 định dạng SMS, Zalo OA và Email.
- `app/prompts/occupancy_report.py`: Phân tích công suất và đề xuất chiến lược giá.

### 2. Thử nghiệm và So sánh 3 Vòng Tối ưu Prompt (Prompt Engineering Iterations)
| Vòng | Phiên bản Prompt | Nhược điểm / Vấn đề phát hiện | Giải pháp cải tiến cho vòng tiếp theo |
|---|---|---|---|
| **Vòng 1 (Cơ bản)** | "Bạn hãy gợi ý sân trống cho khách" | AI hay bịa sân hoặc khung giờ không có trong thực tế (Hallucination). | Bổ sung danh sách `{{available_slots}}` lấy trực tiếp từ CSDL vào context. |
| **Vòng 2 (Ràng buộc CSDL)** | "Chỉ được gợi ý sân có trong danh sách CSDL sau: {{available_slots}}" | Câu trả lời còn khô khan, chưa tư vấn giá giờ thường vs giờ cao điểm. | Bổ sung phân tích giá thuê sau 17h00 và gợi ý sân thay thế nếu hết giờ. |
| **Vòng 3 (Hoàn thiện)** | Tách riêng System Prompt (quy định quy tắc bắt buộc) + User Prompt (dữ liệu + yêu cầu cụ thể). | Kết quả xuất sắc, phản hồi tự nhiên, đầy đủ thông tin giá và nút đặt sân nhanh. | Đạt chuẩn nghiệm thu thực tế, phản hồi chính xác 100% theo dữ liệu CSDL. |

### 3. Xử lý Ngoại lệ và Cơ chế Dự phòng (AI Fallback & Error Handling)
- **Bảo vệ API Key:** Lưu trữ trong biến môi trường `.env`, không hardcode vào mã nguồn.
- **Xử lý Timeout / Rate Limit:** Nếu xảy ra sự cố mất mạng hoặc hết hạn mức API Gemini, hệ thống tự động kích hoạt **Heuristic Rule Engine** nội bộ để sinh câu trả lời logic mà không để ứng dụng bị crash hay báo lỗi khó hiểu cho người dùng.
