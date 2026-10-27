"""
Module Quản lý Prompt: Tự Động Sinh Tin Nhắn / Thông Báo Đặt Sân (Notification Generator)
Đáp ứng tiêu chí KT3: Sinh đa dạng định dạng (SMS ngắn gọn, Zalo thân thiện, Email chi tiết).
"""

SYSTEM_PROMPT = """Bạn là Trợ lý AI phụ trách dịch vụ chăm sóc khách hàng của trung tâm thể thao "Rèn Luyện Thể Hình Trẻ ζɦàղɦ Cɦʊղɕ".
Nhiệm vụ của bạn là tạo các mẫu tin nhắn thông báo (SMS, Zalo, Email) dựa trên thông tin đặt sân cụ thể.

Yêu cầu định dạng:
1. SMS: Ngắn gọn (< 160 ký tự), đầy đủ mã/tên sân, giờ, ngày và số tiền cọc/thanh toán.
2. Zalo: Thân thiện, có biểu tượng cảm xúc (emoji), thông tin rõ ràng, kèm lời nhắc mang giày thể thao phù hợp.
3. Email: Chuyên nghiệp, có tiêu đề (Subject) và nội dung thư trang trọng đầy đủ chi tiết đặt sân, chính sách đổi/hủy lịch trước 2 giờ và hotline hỗ trợ.
"""

def build_notification_user_prompt(booking_info: dict, notification_type: str = "CONFIRMATION") -> str:
    type_labels = {
        "CONFIRMATION": "Xác nhận đặt sân thành công",
        "REMINDER": "Nhắc lịch đặt sân sắp diễn ra (trước 2 tiếng)",
        "CANCELLATION": "Xác nhận hủy lịch đặt sân"
    }
    action_label = type_labels.get(notification_type, "Thông báo đặt sân")

    return f"""Mục đích thông báo: {action_label}

Thông tin lịch đặt sân:
- Mã đặt sân: #{booking_info.get('id')}
- Tên khách hàng: {booking_info.get('customer_name')}
- Số điện thoại: {booking_info.get('customer_phone')}
- Sân thể thao: {booking_info.get('pitch_name')} ({booking_info.get('sport_type')})
- Ngày sử dụng: {booking_info.get('booking_date')}
- Thời gian: {booking_info.get('start_time')} - {booking_info.get('end_time')}
- Tổng tiền: {booking_info.get('total_price', 0):,.0f} VNĐ
- Tiền đã cọc: {booking_info.get('deposit_amount', 0):,.0f} VNĐ
- Tiền còn lại: {(booking_info.get('total_price', 0) - booking_info.get('deposit_amount', 0)):,.0f} VNĐ
- Trạng thái: {booking_info.get('status')}

Hãy tạo 3 định dạng thông báo: SMS, Zalo và Email theo đúng yêu cầu nghiệp vụ.
"""
