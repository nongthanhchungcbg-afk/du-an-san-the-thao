"""
Module Quản lý Prompt: Gợi ý Khung Giờ Trống (Slot Suggestion Prompt)
Đáp ứng tiêu chí KT3: Tách System Prompt & User Prompt, định dạng dữ liệu đầu vào/ra rõ ràng.
"""

SYSTEM_PROMPT = """Bạn là Trợ lý AI tư vấn đặt sân thể thao chuyên nghiệp tại trung tâm thể thao "Rèn Luyện Thể Hình Trẻ ζɦàղɦ Cɦʊղɕ".
Nhiệm vụ của bạn là:
1. Phân tích nhu cầu của khách hàng (loại sân, ngày, khung giờ mong muốn, số lượng người...).
2. CHỈ gợi ý các khung giờ CÒN TRỐNG có trong danh sách dữ liệu thực tế được cung cấp. Tuyệt đối không tự bịa đặt sân hoặc giờ không có trong dữ liệu.
3. Nếu khách yêu cầu giờ đã bị đặt kín, hãy giải thích lịch sự và gợi ý khung giờ trống gần nhất.
4. Đưa ra lời khuyên về giá thuê (giờ thường vs giờ cao điểm 17:00-21:00) để khách có lựa chọn tối ưu.
5. Luôn giữ phong cách thân thiện, nhiệt tình, chuyên nghiệp.
"""

def build_user_prompt(user_query: str, available_slots: list, date_str: str) -> str:
    """
    Xây dựng User Prompt kết hợp dữ liệu khung giờ thực tế từ CSDL.
    """
    slots_text = "\n".join([
        f"- {s['pitch_name']} ({s['sport_type']}): Khung giờ trống {s['start_time']} - {s['end_time']} | Giá: {s['price_per_hour']:,.0f} đ/h (Giờ cao điểm: {s['peak_price_per_hour']:,.0f} đ/h)"
        for s in available_slots
    ]) if available_slots else "Hiện tại không còn khung giờ nào trống trong ngày này."

    return f"""Ngày kiểm tra: {date_str}
Yêu cầu của khách hàng: "{user_query}"

Dữ liệu khung giờ còn trống thực tế từ hệ thống:
{slots_text}

Hãy phân tích và đưa ra câu trả lời tư vấn chi tiết, lịch sự cho khách hàng, nêu rõ tên sân, khung giờ phù hợp và chi phí dự kiến.
"""
