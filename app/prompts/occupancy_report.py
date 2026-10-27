"""
Module Quản lý Prompt: Tóm Tắt Công Suất & Đề Xuất Khuyến Mãi (Occupancy & Promo Strategy)
Đáp ứng tiêu chí KT3: Phân tích số liệu CSDL, nhận diện giờ cao điểm / thấp điểm và sinh chiến lược kinh doanh.
"""

SYSTEM_PROMPT = """Bạn là Chuyên gia AI phân tích kinh doanh và tối ưu hóa vận hành sân thể thao tại "Rèn Luyện Thể Hình Trẻ ζɦàղɦ Cɦʊղɕ".
Nhiệm vụ của bạn là:
1. Đọc số liệu thống kê công suất sử dụng sân thực tế được cung cấp.
2. Nhận xét đánh giá tình hình kinh doanh, công suất trung bình, các ngày và khung giờ cao điểm (thường từ 17h - 21h).
3. Chỉ ra các khung giờ thấp điểm (thường từ 8h - 15h) có tỷ lệ lấp đầy thấp.
4. Đề xuất các chương trình khuyến mãi, voucher hoặc chiến lược giá linh hoạt để thu hút khách hàng vào khung giờ vắng.
5. Cung cấp báo cáo rõ ràng, có cấu trúc bullet point mạch lạc, có tính ứng dụng thực tế cao.
"""

def build_occupancy_user_prompt(stats_data: dict) -> str:
    return f"""Dưới đây là số liệu vận hành và công suất sân trong khoảng thời gian vừa qua:
- Tổng số lượt đặt sân: {stats_data.get('total_bookings', 0)}
- Tổng doanh thu đạt được: {stats_data.get('total_revenue', 0):,.0f} VNĐ
- Tỷ lệ lấp đầy trung bình toàn sân: {stats_data.get('occupancy_rate', 0):.1f}%
- Khung giờ cao điểm nhất: {stats_data.get('peak_hours', '17:00 - 20:30')} (Tỷ lệ lấp đầy: {stats_data.get('peak_occupancy', 88)}%)
- Khung giờ thấp điểm: {stats_data.get('off_peak_hours', '08:00 - 15:00')} (Tỷ lệ lấp đầy: {stats_data.get('off_peak_occupancy', 25)}%)
- Môn thể thao được ưa chuộng nhất: {stats_data.get('top_sport', 'Bóng đá 7 người')}

Chi tiết lượt đặt theo môn:
{stats_data.get('sports_breakdown', 'Bóng đá: 65%, Cầu lông: 25%, Tennis: 10%')}

Hãy viết báo cáo phân tích toàn diện và đề xuất 3 gói khuyến mãi cụ thể để tăng công suất cho các khung giờ thấp điểm.
"""
