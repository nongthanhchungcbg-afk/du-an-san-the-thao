# -*- coding: utf-8 -*-
"""
Generates the modern 16:9 presentation for Group 03 with PERFECT IMAGE ASPECT RATIOS,
PROFESSIONAL FRAMING, AND CLEAN DESIGN RULES.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
from pathlib import Path
from PIL import Image
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation(output_path):
    prs = pptx.Presentation()
    # 16:9 aspect ratio (13.333 x 7.5 inches)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Colors
    NAVY_DARK = RGBColor(15, 23, 42)       # #0F172A
    NAVY_MAIN = RGBColor(30, 58, 138)      # #1E3A8A
    BLUE_ACCENT = RGBColor(37, 99, 235)    # #2563EB
    TEAL_ACCENT = RGBColor(13, 148, 136)   # #0D9488
    GRAY_TEXT = RGBColor(51, 65, 85)       # #334155
    GRAY_LIGHT = RGBColor(248, 250, 252)   # #F8FAFC
    BORDER_COLOR = RGBColor(226, 232, 240) # #E2E8F0
    WHITE = RGBColor(255, 255, 255)

    asset_dir = Path("g:/Du_An_San_The_Thao/slide_assets")
    static_img_dir = Path("g:/Du_An_San_The_Thao/static/images")

    def add_header(slide, title_text, category_text="HỆ THỐNG QUẢN LÝ SÂN THỂ THAO TÍCH HỢP AI"):
        # Top banner line
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.10))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = BLUE_ACCENT
        top_bar.line.fill.background()

        # Category pill
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.28), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = "Segoe UI"
        p_cat.font.size = Pt(10.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = TEAL_ACCENT

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.60), Inches(11.7), Inches(0.75))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = "Segoe UI"
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = NAVY_MAIN

        # Footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.10), Inches(11.7), Inches(0.30))
        tf_f = footer_box.text_frame
        p_f = tf_f.paragraphs[0]
        p_f.text = "Nhóm 03 • Học phần: Ứng dụng Trí tuệ Nhân tạo (AIA331) • GVHD: ThS. Ngô Hữu Huy"
        p_f.font.name = "Segoe UI"
        p_f.font.size = Pt(9.5)
        p_f.font.color.rgb = RGBColor(148, 163, 184)

    def add_card(slide, left, top, width, height, title, items, bg_color=GRAY_LIGHT, border_color=BORDER_COLOR, title_color=NAVY_MAIN, font_size=11.5):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)

        tx_box = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.20), width - Inches(0.50), height - Inches(0.40))
        tf = tx_box.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(font_size + 3.5)
        p_t.font.bold = True
        p_t.font.color.rgb = title_color
        p_t.space_after = Pt(10)

        for item in items:
            p = tf.add_paragraph()
            p.text = f"•  {item}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(font_size)
            p.font.color.rgb = GRAY_TEXT
            p.space_after = Pt(6)

    def add_clean_image(slide, box_left, box_top, box_width, box_height, image_path, caption=""):
        """
        Renders an image strictly preserving its original aspect ratio,
        wrapped with a clean, razor-sharp modern frame and centered caption.
        NO STRETCHING, NO DISTORTION.
        """
        if not os.path.exists(str(image_path)):
            return

        with Image.open(str(image_path)) as im:
            orig_w, orig_h = im.size

        aspect = orig_w / orig_h

        # Height reserved for caption if provided
        cap_h = Inches(0.38) if caption else Inches(0)
        avail_h = box_height - cap_h
        avail_w = box_width

        # Determine dimensions while strictly preserving aspect ratio
        avail_aspect = avail_w / avail_h
        if aspect > avail_aspect:
            # Width is constraining
            fitted_w = avail_w
            fitted_h = avail_w / aspect
        else:
            # Height is constraining
            fitted_h = avail_h
            fitted_w = avail_h * aspect

        # Center inside bounding box
        offset_x = (box_width - fitted_w) / 2
        offset_y = (avail_h - fitted_h) / 2

        img_left = box_left + offset_x
        img_top = box_top + offset_y

        # Elegant outer frame with subtle padding
        frame = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            img_left - Inches(0.04),
            img_top - Inches(0.04),
            fitted_w + Inches(0.08),
            fitted_h + Inches(0.08)
        )
        frame.fill.solid()
        frame.fill.fore_color.rgb = WHITE
        frame.line.color.rgb = RGBColor(203, 213, 225) # Slate 300
        frame.line.width = Pt(1)

        # Place image strictly with fitted dimensions
        slide.shapes.add_picture(str(image_path), img_left, img_top, width=fitted_w, height=fitted_h)

        # Caption placed cleanly below image
        if caption:
            c_top = img_top + fitted_h + Inches(0.06)
            cap_box = slide.shapes.add_textbox(box_left, c_top, box_width, Inches(0.32))
            tf_c = cap_box.text_frame
            tf_c.word_wrap = True
            p_c = tf_c.paragraphs[0]
            p_c.text = caption
            p_c.font.name = "Segoe UI"
            p_c.font.size = Pt(10)
            p_c.font.italic = True
            p_c.font.bold = True
            p_c.font.color.rgb = RGBColor(71, 85, 105) # Slate 600
            p_c.alignment = PP_ALIGN.CENTER

    # ==================== SLIDE 1: TITLE SLIDE ====================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY_DARK
    bg1.line.fill.background()

    dec_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.1), Inches(0.12), Inches(5.2))
    dec_bar.fill.solid()
    dec_bar.fill.fore_color.rgb = BLUE_ACCENT
    dec_bar.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.1), Inches(1.0), Inches(7.3), Inches(5.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG (ICTU)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT
    p.space_after = Pt(8)

    p = tf1.add_paragraph()
    p.text = "BÁO CÁO TIỂU LUẬN HỌC PHẦN: ỨNG DỤNG TRÍ TUỆ NHÂN TẠO (AIA331)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_after = Pt(16)

    p = tf1.add_paragraph()
    p.text = "HỆ THỐNG QUẢN LÝ SÂN THỂ THAO\nCHO THUÊ TÍCH HỢP AI"
    p.font.name = "Segoe UI"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.space_after = Pt(22)

    p = tf1.add_paragraph()
    p.text = "NHÓM THỰC HIỆN: NHÓM 03  |  LỚP: CNTT K23M"
    p.font.name = "Segoe UI"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p.space_after = Pt(8)

    p = tf1.add_paragraph()
    p.text = "• Sinh viên: Nông Thành Chung (NT)  • Nguyễn Văn Lộc  • Hoàng Trí Tường\n• Giảng viên hướng dẫn: ThS. Ngô Hữu Huy"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(226, 232, 240)
    p.space_after = Pt(10)

    p = tf1.add_paragraph()
    p.text = "Thái Nguyên, Năm 2026"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11)
    p.font.italic = True
    p.font.color.rgb = RGBColor(148, 163, 184)

    # Right Image: Real Sport Pitch image (fitted with correct aspect ratio)
    pitch_img = static_img_dir / "pitch-01.jpg"
    if pitch_img.exists():
        add_clean_image(s1, Inches(8.6), Inches(1.2), Inches(3.9), Inches(5.0), pitch_img, "Cụm Sân Thể Thao Tích Hợp AI")

    # ==================== SLIDE 2: AGENDA ====================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Nội Dung Báo Cáo Trọng Tâm")
    add_card(s2, Inches(0.8), Inches(1.65), Inches(3.6), Inches(2.4), "01. Tổng Quan & Mục Tiêu", [
        "Thực trạng quản lý sân truyền thống",
        "Mục tiêu số hóa & tối ưu vận hành",
        "Phạm vi và đối tượng người dùng"
    ])
    add_card(s2, Inches(4.8), Inches(1.65), Inches(3.6), Inches(2.4), "02. Công Nghệ & Kiến Trúc", [
        "Kiến trúc phân tầng FastAPI + ORM",
        "Frontend Jinja2 & Bootstrap hiện đại",
        "OpenAI / Gemini LLM Integration"
    ])
    add_card(s2, Inches(8.8), Inches(1.65), Inches(3.6), Inches(2.4), "03. Phân Tích & Phân Quyền", [
        "Phân quyền 3 tác nhân (Admin, Staff, User)",
        "Quy trình đặt sân & chống trùng lịch",
        "Thiết kế CSDL quan hệ chuẩn hóa"
    ])
    add_card(s2, Inches(0.8), Inches(4.45), Inches(3.6), Inches(2.4), "04. 3 Chức Năng AI Đột Phá", [
        "AI Gợi ý khung giờ trống thông minh",
        "AI Sinh tin nhắn xác nhận & nhắc lịch",
        "AI Tóm tắt công suất & gợi ý voucher"
    ])
    add_card(s2, Inches(4.8), Inches(4.45), Inches(3.6), Inches(2.4), "05. Vòng Đời SDLC & Prompt", [
        "Prompt Engineering & chống Hallucination",
        "Chế độ Fallback offline an toàn",
        "Minh chứng AI trong Code, Test, Doc"
    ])
    add_card(s2, Inches(8.8), Inches(4.45), Inches(3.6), Inches(2.4), "06. Demo, Đánh Giá & Tương Lai", [
        "Kiểm thử tự động Pytest 100% Pass",
        "Giao diện Dashboard & đặt sân thực tế",
        "Hướng mở rộng thanh toán QR & Mobile"
    ])

    # ==================== SLIDE 3: PROBLEM STATEMENT WITH PROPER DIAGRAM ====================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Đặt Vấn Đề & Nghiệp Vụ Cốt Lõi")
    add_card(s3, Inches(0.8), Inches(1.65), Inches(5.2), Inches(5.1), "⚠️ Thách Thức Quản Lý Truyền Thống", [
        "Quản lý bằng sổ sách, Excel hoặc Zalo riêng lẻ dẫn đến thất thoát dữ liệu.",
        "Xung đột & trùng lịch (Double Booking) thường xuyên xảy ra trong các khung giờ vàng.",
        "Nhân viên lễ tân tốn 2 - 3 giờ mỗi ngày để nhắn tin xác nhận và nhắc cọc thủ công.",
        "Chủ sân khó nắm bắt tỷ lệ lấp đầy, thiếu chiến lược kích cầu vào giờ vắng khách.",
        "Khách hàng mất nhiều thời gian gọi điện hỏi xem còn sân trống hay không."
    ], bg_color=RGBColor(254, 242, 242), border_color=RGBColor(254, 202, 202), title_color=RGBColor(185, 28, 28), font_size=11.5)

    add_clean_image(s3, Inches(6.3), Inches(1.65), Inches(6.2), Inches(5.1), asset_dir / "image2.png", "Hình 1.1: Sơ đồ các nghiệp vụ cốt lõi của sân thể thao")

    # ==================== SLIDE 4: OBJECTIVES & SCOPE ====================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Mục Tiêu & Phạm Vi Đề Tài")
    add_card(s4, Inches(0.8), Inches(1.65), Inches(3.6), Inches(5.1), "🎯 Mục Tiêu Nghiệp Vụ", [
        "Tin học hóa 100% quy trình từ tra cứu, đặt cọc, check-in đến thanh toán.",
        "Giảm 80% thời gian xử lý đơn đặt sân của nhân viên lễ tân.",
        "Nâng cao tỷ lệ khai thác sân vào các khung giờ thấp điểm (9h - 16h).",
        "Tạo trải nghiệm hiện đại, thuận tiện cho người chơi thể thao."
    ])
    add_card(s4, Inches(4.8), Inches(1.65), Inches(3.6), Inches(5.1), "🤖 Mục Tiêu Ứng Dụng AI", [
        "Ứng dụng Large Language Models (LLM) giải quyết bài toán nghiệp vụ thực tiễn.",
        "Tối ưu Prompt Engineering: Zero-shot, Few-shot, Role-based, JSON Output.",
        "Áp dụng AI vào chu trình phát triển phần mềm (SDLC): Phân tích, sinh code, viết test."
    ])
    add_card(s4, Inches(8.8), Inches(1.65), Inches(3.6), Inches(5.1), "📌 Phạm Vi Triển Khai", [
        "Loại hình sân: Bóng đá 5-7 người, Cầu lông, Pickleball, Tennis.",
        "Mô hình vận hành: Quản lý theo cụm sân với các khung giờ chuẩn linh hoạt.",
        "Khả năng mở rộng: Sẵn sàng kết nối cổng thanh toán trực tuyến và ứng dụng di động."
    ])

    # ==================== SLIDE 5: TECH STACK & ARCHITECTURE DIAGRAM ====================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Kiến Trúc Công Nghệ & Sơ Đồ Hệ Thống")
    add_card(s5, Inches(0.8), Inches(1.65), Inches(4.8), Inches(5.1), "⚡ Công Nghệ Nền Tảng", [
        "Backend FastAPI: Hiệu năng bất đồng bộ cao, Swagger UI tự động tại /docs.",
        "Frontend Jinja2 + Bootstrap 5: Giao diện Responsive hiện đại trên mọi thiết bị.",
        "CSDL SQLite / PostgreSQL: Kết hợp SQLAlchemy 2.0 ORM và quản lý Transaction.",
        "AI Layer: OpenAI GPT-3.5/GPT-4o & Google Gemini Pro.",
        "Chế độ Fallback Heuristic: Đảm bảo chạy mượt 100% ngay cả khi mất mạng."
    ], font_size=11.5)

    add_clean_image(s5, Inches(5.9), Inches(1.65), Inches(6.6), Inches(5.1), asset_dir / "image20.png", "Hình 2.3: Sơ đồ kiến trúc tổng thể các tầng hệ thống")

    # ==================== SLIDE 6: ACTORS & USE CASE DIAGRAM ====================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Mô Hình Tác Nhân & Sơ Đồ Use Case Tổng Quát")
    add_card(s6, Inches(0.8), Inches(1.65), Inches(4.8), Inches(5.1), "👥 3 Tác Nhân Chính (RBAC)", [
        "👑 Quản Trị Viên (Admin): Toàn quyền quản trị sân, bảng giá, xem báo cáo doanh thu & gợi ý chiến lược AI.",
        "💼 Nhân Viên (Lễ Tân): Tiếp nhận đơn đặt sân tại quầy, thu cọc, đổi/hủy lịch, sinh tin nhắn thông báo AI gửi khách.",
        "⚽ Khách Hàng: Xem lịch trực quan, nhờ AI tư vấn giờ trống, đặt sân và xem lịch sử đơn cá nhân."
    ], bg_color=RGBColor(245, 243, 255), border_color=RGBColor(221, 214, 254), title_color=RGBColor(109, 40, 217), font_size=11.5)

    add_clean_image(s6, Inches(5.9), Inches(1.65), Inches(6.6), Inches(5.1), asset_dir / "image9.png", "Hình 2.1: Biểu đồ Use Case tổng quát hệ thống")

    # ==================== SLIDE 7: SEQUENCE DIAGRAM & CONFLICT ERROR UI ====================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Quy Trình Nghiệp Vụ & Chống Trùng Lịch Thực Tế")
    add_card(s7, Inches(0.8), Inches(1.65), Inches(4.6), Inches(5.1), "🛡️ Chống Trùng Lịch Tuyệt Đối", [
        "Vấn đề: 2 khách hàng cùng đặt 1 slot vào cùng thời điểm.",
        "Giải pháp kỹ thuật: Áp dụng Transaction Lock trong SQLAlchemy.",
        "Kiểm tra điều kiện: pitch_id = X AND slot_time = Y AND status != 'CANCELLED'.",
        "Nếu trùng lặp: Rollback ngay lập tức, trả mã lỗi HTTP 400 Bad Request kèm thông báo thân thiện.",
        "Được kiểm thử tự động với Pytest đạt độ tin cậy 100%."
    ], bg_color=RGBColor(254, 242, 242), border_color=RGBColor(254, 202, 202), title_color=RGBColor(185, 28, 28), font_size=11)

    add_clean_image(s7, Inches(5.7), Inches(1.65), Inches(6.8), Inches(2.45), asset_dir / "image15.png", "Hình 2.7: Sơ đồ tuần tự Đặt sân và Chống trùng lịch")
    add_clean_image(s7, Inches(5.7), Inches(4.30), Inches(6.8), Inches(2.45), asset_dir / "image29.png", "Hình 3.7.4: Giao diện thực tế cảnh báo lỗi trùng lịch")

    # ==================== SLIDE 8: AI FEATURE 1 WITH PROPER ASPECT RATIO ====================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Tính Năng AI 1: Gợi Ý Khung Giờ Còn Trống Thông Minh")
    add_card(s8, Inches(0.8), Inches(1.65), Inches(4.6), Inches(5.1), "💬 Tư Vấn Bằng Ngôn Ngữ Tự Nhiên", [
        "Khách hỏi tự nhiên: 'Tối nay khoảng 18h-20h nhóm mình muốn đá bóng sân 7, có sân nào trống giá hợp lý không?'",
        "Cơ chế AI xử lý:",
        "1. AI trích xuất thực thể: Thể loại, Ngày, Khung giờ mong muốn.",
        "2. Hệ thống truy vấn các slot THỰC SỰ TRỐNG trong database SQLite.",
        "3. Đưa danh sách slot làm Ground Truth Context vào Prompt.",
        "4. AI phản hồi tự nhiên, giới thiệu sân kèm giá tiền và nút 'Đặt ngay'."
    ], font_size=11)

    # Correctly fitted image preserving exact 2.08:1 aspect ratio!
    add_clean_image(s8, Inches(5.7), Inches(1.65), Inches(6.8), Inches(5.1), asset_dir / "image30.png", "Hình 3.7.5: Giao diện thực tế AI tư vấn và gợi ý khung giờ còn trống")

    # ==================== SLIDE 9: AI FEATURE 2 WITH PROPER ASPECT RATIO ====================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Tính Năng AI 2: Tự Động Sinh Tin Nhắn Đa Kênh")
    add_card(s9, Inches(0.8), Inches(1.65), Inches(4.6), Inches(5.1), "📱 3 Định Dạng Thông Báo Tự Động", [
        "1. Kênh SMS (Ngắn Gọn): Tập trung mã đặt sân, thời gian, số tiền cọc (<160 ký tự), tiết kiệm chi phí.",
        "2. Kênh Zalo OA (Thân Thiện): Giọng điệu ấm áp, trẻ trung, có emoji chúc trận đấu thăng hoa.",
        "3. Kênh Email (Trang Trọng): Đầy đủ hóa đơn, điều khoản check-in trước 15 phút và chính sách hủy lịch.",
        "Tính năng '1-Click Copy' giúp lễ tân gửi tin nhắn cho khách chỉ trong 3 giây."
    ], bg_color=RGBColor(239, 246, 255), border_color=RGBColor(191, 219, 254), title_color=BLUE_ACCENT, font_size=11)

    add_clean_image(s9, Inches(5.7), Inches(1.65), Inches(6.8), Inches(5.1), asset_dir / "image31.png", "Hình 3.7.6: Giao diện thực tế AI sinh tin nhắn 3 tab SMS, Zalo OA, Email")

    # ==================== SLIDE 10: AI FEATURE 3 WITH PROPER ASPECT RATIO ====================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Tính Năng AI 3: Báo Cáo Công Suất & Đề Xuất Khuyến Mại")
    add_card(s10, Inches(0.8), Inches(1.65), Inches(5.2), Inches(5.1), "📊 Phân Tích Công Suất & Tự Động Sinh Voucher", [
        "Thống kê tự động: Giờ cao điểm (17h30-21h30) kín chỗ (95-100%), giờ thấp điểm (8h-16h) chỉ đạt 20-35%.",
        "AI phân tích công suất và tự động đề xuất voucher kích cầu:",
        "• Voucher 'Học Sinh - Sinh Viên': Giảm 30% giá sân khung 13h - 16h.",
        "• Combo 'Nước Uống Miễn Phí': Cho đội đá cố định buổi sáng.",
        "• Chủ sân chỉ cần 1 click để kích hoạt mã khuyến mại lên hệ thống."
    ], bg_color=RGBColor(254, 243, 199), border_color=RGBColor(253, 230, 138), title_color=RGBColor(180, 83, 9), font_size=11.5)

    add_clean_image(s10, Inches(6.3), Inches(1.65), Inches(6.2), Inches(5.1), asset_dir / "image32.png", "Hình 3.7.7: Giao diện thực tế AI phân tích công suất và đề xuất khuyến mãi")

    # ==================== SLIDE 11: PROMPT ENGINEERING WITH PROPER DIAGRAM ====================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Thiết Kế Prompt Engineering & Chế Độ Fallback")
    add_card(s11, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.1), "🧠 Cấu Trúc Prompt Chuyên Nghiệp", [
        "1. Role Definition: Định nghĩa vai trò chuyên viên lễ tân / trợ lý kinh doanh.",
        "2. Strict Constraints: Ràng buộc KHÔNG được bịa slot trống ngoài dữ liệu được cấp.",
        "3. Few-shot Examples: Cung cấp mẫu câu hỏi và phản hồi chuẩn mẫu.",
        "4. Structured JSON Output: Xuất định dạng chuẩn để Backend parse dữ liệu chính xác.",
        "5. Cơ chế Heuristic Fallback: Tự động chạy thuật toán Rule-based nội bộ khi mất mạng hoặc không có API Key."
    ], font_size=11.5)

    add_clean_image(s11, Inches(6.7), Inches(1.65), Inches(5.8), Inches(5.1), asset_dir / "image4.png", "Hình 1.4: Cấu trúc Prompt hiệu quả được áp dụng")

    # ==================== SLIDE 12: SDLC ====================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Ứng Dụng AI Trong Vòng Đời Phần Mềm (SDLC)")
    add_card(s12, Inches(0.8), Inches(1.65), Inches(3.6), Inches(2.4), "1. Phân Tích Yêu Cầu", [
        "AI gợi ý User Stories chuẩn.",
        "Xây dựng ma trận chức năng.",
        "Xác định rủi ro kinh doanh."
    ])
    add_card(s12, Inches(4.8), Inches(1.65), Inches(3.6), Inches(2.4), "2. Thiết Kế Hệ Thống", [
        "Chuẩn hóa mô hình ERD 3NF.",
        "Thiết kế cấu trúc Restful API.",
        "Vẽ luồng dữ liệu chống trùng lịch."
    ])
    add_card(s12, Inches(8.8), Inches(1.65), Inches(3.6), Inches(2.4), "3. Lập Trình & Sinh Code", [
        "AI sinh boilerplate CRUD FastAPI.",
        "Tạo Pydantic Schemas và Models.",
        "Viết script nạp dữ liệu mẫu seed_data."
    ])
    add_card(s12, Inches(0.8), Inches(4.45), Inches(3.6), Inches(2.4), "4. Phát Hiện Lỗi & Tối Ưu", [
        "Phát hiện lỗi Race Condition.",
        "Tối ưu câu truy vấn SQLAlchemy.",
        "Cải thiện giao diện responsive."
    ])
    add_card(s12, Inches(4.8), Inches(4.45), Inches(3.6), Inches(2.4), "5. Kiểm Thử Tự Động", [
        "AI sinh test cases biên Pytest.",
        "Giả lập người dùng đặt trùng giờ.",
        "Kiểm thử bảo mật SQLi & XSS."
    ])
    add_card(s12, Inches(8.8), Inches(4.45), Inches(3.6), Inches(2.4), "6. Viết Tài Liệu & Slide", [
        "Tổng hợp báo cáo tiểu luận Word.",
        "Thiết kế slide trình chiếu chuyên nghiệp.",
        "Xây dựng hướng dẫn cài đặt chi tiết."
    ])

    # ==================== SLIDE 13: DATABASE ERD DIAGRAM ====================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Thiết Kế Cơ Sở Dữ Liệu (Mô Hình ERD)")
    add_card(s13, Inches(0.8), Inches(1.65), Inches(4.6), Inches(5.1), "🗄️ Cấu Trúc Các Bảng Dữ Liệu", [
        "• users: Tài khoản, phân quyền (admin, staff, user), băm mật khẩu bcrypt.",
        "• pitch_types & pitches: Thông tin loại sân, kích thước, cụm sân, trạng thái bảo trì.",
        "• time_slots: Khung giờ chuẩn theo ngày (giờ vàng vs giờ thường).",
        "• bookings & payments: Đơn đặt sân, mã booking duy nhất, tiền cọc, phương thức thanh toán.",
        "• maintenance: Lịch bảo dưỡng thiết bị tự động khóa slot."
    ], font_size=11.5)

    add_clean_image(s13, Inches(5.7), Inches(1.65), Inches(6.8), Inches(5.1), asset_dir / "image19.png", "Hình 2.2: Sơ đồ thực thể - quan hệ (ERD) cơ sở dữ liệu")

    # ==================== SLIDE 14: REAL UI DEMO SHOWCASE ====================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Giao Diện Hệ Thống Thực Tế (Showcase)")
    add_clean_image(s14, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.1), asset_dir / "image28.png", "Hình 3.7.3: Giao diện đặt sân trực quan theo ma trận lịch")
    add_clean_image(s14, Inches(6.8), Inches(1.65), Inches(5.7), Inches(5.1), asset_dir / "image27.png", "Hình 3.7.2: Giao diện quản lý sân và cấu hình giá")

    # ==================== SLIDE 15: TESTING & STATS REPORT UI ====================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "Kiểm Thử Tự Động & Báo Cáo Thống Kê Thực Tế")
    add_card(s15, Inches(0.8), Inches(1.65), Inches(4.8), Inches(5.1), "🧪 Kết Quả Kiểm Thử (Pytest)", [
        "• 100% Test cases đạt trạng thái PASSED:",
        "   ✅ Kiểm thử xác thực JWT & Phân quyền vai trò.",
        "   ✅ Kiểm thử chống đặt trùng lịch (Double Booking).",
        "   ✅ Kiểm thử tính giá tiền giờ cao điểm/thấp điểm.",
        "   ✅ Kiểm thử AI Service & Fallback an toàn.",
        "• Thời gian phản hồi API CRUD: < 80ms.",
        "• Giao diện báo cáo số liệu doanh thu và tỷ lệ sử dụng sân trực quan bằng biểu đồ."
    ], bg_color=RGBColor(240, 253, 244), border_color=RGBColor(187, 247, 208), title_color=RGBColor(21, 128, 61), font_size=11)

    add_clean_image(s15, Inches(5.9), Inches(1.65), Inches(6.6), Inches(5.1), asset_dir / "image33.png", "Hình 3.7.8: Giao diện thực tế báo cáo thống kê doanh thu và tỷ lệ đặt sân")

    # ==================== SLIDE 16: PROS & CONS ====================
    s16 = prs.slides.add_slide(blank_layout)
    add_header(s16, "Đánh Giá Ưu Điểm & Hạn Chế Của Đề Tài")
    add_card(s16, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.1), "🌟 Ưu Điểm Nổi Bật", [
        "Bám sát thực tế: Giải quyết triệt để vấn đề trùng lịch và thất thoát doanh thu.",
        "Ứng dụng AI thực chất: 3 chức năng AI gắn chặt với nghiệp vụ kinh doanh sân.",
        "Kiến trúc sạch sẽ: Phân tầng module hóa (models, schemas, services, routers).",
        "Triển khai cực kỳ đơn giản: Chỉ cần 1-click vào file 'run.bat' là chạy ngay.",
        "Đầy đủ tài khoản đăng nhập mẫu 1 chạm, giao diện hiện đại trên cả Mobile."
    ], bg_color=RGBColor(240, 253, 250), border_color=RGBColor(153, 246, 228), title_color=TEAL_ACCENT, font_size=12)

    add_card(s16, Inches(6.8), Inches(1.65), Inches(5.7), Inches(5.1), "🔍 Hạn Chế Cần Hoàn Thiện", [
        "Hiện tại sử dụng SQLite phục vụ thử nghiệm cục bộ trên đĩa CD.",
        "Chức năng gửi tin nhắn SMS / Zalo thực tế cần đăng ký tài khoản Doanh nghiệp trả phí.",
        "Chưa tích hợp trực tiếp Webhook ngân hàng tự động đối soát tiền cọc khi khách chuyển khoản."
    ], bg_color=RGBColor(255, 251, 235), border_color=RGBColor(253, 230, 138), title_color=RGBColor(180, 83, 9), font_size=12)

    # ==================== SLIDE 17: FUTURE WORK ====================
    s17 = prs.slides.add_slide(blank_layout)
    add_header(s17, "Định Hướng Phát Triển Trong Tương Lai")
    add_card(s17, Inches(0.8), Inches(1.65), Inches(3.6), Inches(5.1), "💳 Thanh Toán VietQR Tự Động", [
        "Tích hợp mã QR động theo từng đơn đặt sân.",
        "Tự động điền số tiền cọc và nội dung mã đơn.",
        "Xác nhận thanh toán tự động qua Webhook ngân hàng không cần lễ tân bấm tay."
    ])
    add_card(s17, Inches(4.8), Inches(1.65), Inches(3.6), Inches(5.1), "🤖 Chatbot Realtime Đa Kênh", [
        "Đưa AI Service kết nối trực tiếp vào Zalo OA và Fanpage Facebook của sân.",
        "Khách có thể chat trực tiếp trên Zalo/Messenger để đặt sân và nhận mã vé điện tử.",
        "Tự động giải đáp thắc mắc 24/7."
    ], bg_color=RGBColor(239, 246, 255), border_color=RGBColor(191, 219, 254), title_color=BLUE_ACCENT)

    add_card(s17, Inches(8.8), Inches(1.65), Inches(3.6), Inches(5.1), "📹 Camera AI & Chuỗi Sân", [
        "Camera AI nhận diện biển số xe của khách tại bãi để tự động check-in vào sân.",
        "Mở rộng kiến trúc SaaS phục vụ hàng trăm chuỗi sân thể thao trên toàn quốc."
    ])

    # ==================== SLIDE 18: CONCLUSION ====================
    s18 = prs.slides.add_slide(blank_layout)
    bg18 = s18.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg18.fill.solid()
    bg18.fill.fore_color.rgb = NAVY_DARK
    bg18.line.fill.background()

    tb18 = s18.shapes.add_textbox(Inches(1.5), Inches(1.5), Inches(10.333), Inches(4.5))
    tf18 = tb18.text_frame
    tf18.word_wrap = True

    p = tf18.paragraphs[0]
    p.text = "KẾT LUẬN & LỜI CẢM ƠN"
    p.font.name = "Segoe UI"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(20)

    p = tf18.add_paragraph()
    p.text = "Đề tài đã hoàn thành xuất sắc các mục tiêu đề ra: Xây dựng hệ thống quản lý sân thể thao toàn diện, giải quyết triệt để vấn đề trùng lịch và ứng dụng Trí tuệ nhân tạo (AI) một cách thiết thực, hiệu quả."
    p.font.name = "Segoe UI"
    p.font.size = Pt(16)
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(24)

    p = tf18.add_paragraph()
    p.text = "Nhóm 03 xin trân trọng gửi lời cảm ơn sâu sắc tới ThS. Ngô Hữu Huy đã luôn tận tình định hướng và hỗ trợ nhóm trong suốt học phần!"
    p.font.name = "Segoe UI"
    p.font.size = Pt(15)
    p.font.italic = True
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(36)

    p = tf18.add_paragraph()
    p.text = "XIN CHÂN THÀNH CẢM ƠN THẦY VÀ CÁC BẠN ĐÃ LẮNG NGHE!\nQ&A - MỜI THẦY VÀ CÁC BẠN ĐẶT CÂU HỎI"
    p.font.name = "Segoe UI"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p.alignment = PP_ALIGN.CENTER

    prs.save(output_path)
    print(f"Presentation regenerated with PERFECT ASPECT RATIO at: {output_path}")

if __name__ == "__main__":
    out_file = "g:/Du_An_San_The_Thao/DIA_CD_NHOM_03/02_Slide_Bao_Cao/NHOM_03_Slide_Thuyet_Trinh_He_Thong_Quan_Ly_San_The_Thao_AI.pptx"
    create_presentation(out_file)
