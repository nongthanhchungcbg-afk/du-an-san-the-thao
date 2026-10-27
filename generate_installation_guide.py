# -*- coding: utf-8 -*-
"""
Generates professional Installation Guide documents (DOCX and MD)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def create_installation_guide_docx(output_path):
    doc = docx.Document()

    # Page Margins: 2cm all sides
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.9)
        s.right_margin = Inches(0.9)

    # Styles
    COLOR_PRIMARY = RGBColor(30, 58, 138)   # Deep Navy #1E3A8A
    COLOR_SECONDARY = RGBColor(13, 148, 136) # Teal #0D9488
    COLOR_TEXT = RGBColor(30, 41, 59)       # Dark Slate #1E293B

    # Header / University
    p_uni = doc.add_paragraph()
    p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_uni = p_uni.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG (ICTU)")
    r_uni.font.name = "Times New Roman"
    r_uni.font.size = Pt(12)
    r_uni.font.bold = True
    r_uni.font.color.rgb = COLOR_PRIMARY

    p_div = doc.add_paragraph()
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_div = p_div.add_run("-------------------***-------------------")
    r_div.font.name = "Times New Roman"
    r_div.font.size = Pt(11)

    # Main Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("HƯỚNG DẪN CÀI ĐẶT VÀ VẬN HÀNH\nCHƯƠNG TRÌNH THỬ NGHIỆM")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(6)

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("ĐỀ TÀI: HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CHO THUÊ TÍCH HỢP AI\n")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(13)
    r_sub.font.bold = True
    r_sub.font.color.rgb = COLOR_SECONDARY
    
    r_sub2 = p_sub.add_run("Học phần: Ứng dụng Trí tuệ Nhân tạo (AIA331) - Nhóm 03 - Lớp: CNTT K23M")
    r_sub2.font.name = "Times New Roman"
    r_sub2.font.size = Pt(12)
    r_sub2.font.italic = True
    p_sub.paragraph_format.space_after = Pt(14)

    # Info Table
    t_info = doc.add_table(rows=5, cols=2)
    t_info.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_data = [
        ("Giảng viên hướng dẫn:", "ThS. Ngô Hữu Huy"),
        ("Nhóm sinh viên thực hiện:", "NHÓM 03"),
        ("Các thành viên đề tài:", "1. Nông Thành Chung (Nhóm trưởng)\n2. Nguyễn Văn Lộc\n3. Hoàng Trí Tường"),
        ("Mã học phần:", "AIA331 - Ứng dụng Trí tuệ Nhân tạo"),
        ("Thời gian thực hiện:", "Năm học 2025 - 2026 (ICTU Thái Nguyên)")
    ]
    for idx, (label, val) in enumerate(info_data):
        row = t_info.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.5)
        set_cell_margins(c0)
        set_cell_margins(c1)
        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "FFFFFF")
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(label)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(11)
        r0.font.bold = True
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(val)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(11)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    def add_sec_heading(title_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(title_text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_p(text, bold_prefix="", italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = "Times New Roman"
            rb.font.size = Pt(11)
            rb.font.bold = True
            rb.font.color.rgb = COLOR_TEXT
        rt = p.add_run(text)
        rt.font.name = "Times New Roman"
        rt.font.size = Pt(11)
        rt.font.italic = italic
        rt.font.color.rgb = COLOR_TEXT
        return p

    def add_code_block(code_text):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.rows[0].cells[0]
        cell.width = Inches(6.7)
        set_cell_background(cell, "F8FAFC")
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(code_text)
        r.font.name = "Consolas"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(15, 23, 42)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 1. TỔNG QUAN
    add_sec_heading("1. TỔNG QUAN VỀ HỆ THỐNG THỬ NGHIỆM")
    add_p(" Hệ thống được xây dựng nhằm tin học hóa và thông minh hóa toàn diện quy trình quản lý sân thể thao cho thuê (bóng đá, cầu lông, tennis, pickleball).", "• Tôn chỉ phát triển:")
    add_p(" Ngăn chặn triệt để tình trạng đặt trùng lịch nhờ cơ chế Transaction Lock của cơ sở dữ liệu.", "• Điểm cốt lõi 1:")
    add_p(" Tích hợp 3 chức năng Trí tuệ nhân tạo (AI): Gợi ý khung giờ còn trống từ ngôn ngữ tự nhiên; Tự động sinh tin nhắn xác nhận & nhắc lịch đa kênh (SMS, Zalo OA, Email); Báo cáo tỷ lệ công suất và đề xuất voucher khuyến mại giờ thấp điểm.", "• Điểm cốt lõi 2:")
    add_p(" Hỗ trợ chế độ AI Fallback thông minh, cho phép hệ thống hoạt động ổn định 100% ngay cả khi thiết bị thử nghiệm không có kết nối Internet hoặc chưa cấu hình API Key.", "• Điểm cốt lõi 3:")

    # 2. YÊU CẦU CẤU HÌNH
    add_sec_heading("2. YÊU CẦU CẤU HÌNH PHẦN CỨNG VÀ PHẦN MỀM")
    t_req = doc.add_table(rows=6, cols=3)
    t_req.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Thành phần", "Yêu cầu tối thiểu", "Khuyến nghị"]
    for i, h in enumerate(headers):
        cell = t_req.rows[0].cells[i]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    req_data = [
        ("Hệ điều hành", "Windows 10 / Linux / macOS", "Windows 10/11 (64-bit)"),
        ("Môi trường Python", "Python 3.10 trở lên", "Python 3.11, 3.12 hoặc 3.13"),
        ("Bộ nhớ RAM", "Tối thiểu 2 GB", "4 GB RAM trở lên"),
        ("Dung lượng ổ đĩa", "Tối thiểu 300 MB trống", "1 GB SSD trống"),
        ("Trình duyệt web", "Mọi trình duyệt hiện đại", "Google Chrome, MS Edge, Firefox"),
    ]
    for r_idx, row_values in enumerate(req_data, start=1):
        row = t_req.rows[r_idx]
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_values):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 3. NGUỒN THAM KHẢO
    add_sec_heading("3. NGUỒN TÀI LIỆU THAM KHẢO CHÍNH THỐNG")
    add_p("Các thư viện và công nghệ trong dự án được xây dựng dựa trên các tài liệu chuẩn quốc tế sau:")
    refs = [
        ("[1] FastAPI Framework Documentation:", " Tài liệu chính thức về xây dựng Web API bất đồng bộ hiệu năng cao với Python. Truy cập: https://fastapi.tiangolo.com/"),
        ("[2] Uvicorn ASGI Server:", " Chuẩn giao tiếp máy chủ web ASGI siêu tốc độ dành cho ứng dụng Python. Truy cập: https://www.uvicorn.org/"),
        ("[3] SQLAlchemy 2.0 ORM Documentation:", " Hướng dẫn thiết kế tầng truy cập dữ liệu, mô hình quan hệ và quản trị giao dịch ACID. Truy cập: https://docs.sqlalchemy.org/"),
        ("[4] OpenAI API & Prompt Engineering Guide:", " Tài liệu hướng dẫn thiết kế câu lệnh có cấu trúc (Prompt Engineering) và tích hợp mô hình ngôn ngữ lớn LLM. Truy cập: https://platform.openai.com/docs/"),
        ("[5] Google Gemini API Documentation:", " Tài liệu tích hợp mô hình AI đa phương thức và sinh văn bản tiếng Việt của Google AI. Truy cập: https://ai.google.dev/"),
        ("[6] Jinja2 Template Designer Documentation:", " Tài liệu thiết kế hệ thống giao diện mẫu động phía máy chủ. Truy cập: https://jinja.palletsprojects.com/"),
        ("[7] Bootstrap 5 Framework:", " Thư viện thành phần giao diện chuẩn Responsive cho đa nền tảng thiết bị. Truy cập: https://getbootstrap.com/"),
        ("[8] Pytest Framework Documentation:", " Khung kiểm thử tự động toàn diện dành cho mã nguồn Python. Truy cập: https://docs.pytest.org/"),
        ("[9] Pydantic Data Validation:", " Thư viện phân tích cú pháp và xác thực dữ liệu đầu vào. Truy cập: https://docs.pydantic.dev/")
    ]
    for pref, desc in refs:
        add_p(desc, bold_prefix=pref)

    # 4. DANH SÁCH GÓI THƯ VIỆN
    add_sec_heading("4. CÁC GÓI THƯ VIỆN VÀ VAI TRÒ TRONG DỰ ÁN (requirements.txt)")
    add_p("Toàn bộ các gói phụ thuộc được khai báo trong file requirements.txt, bao gồm:")
    
    t_lib = doc.add_table(rows=12, cols=3)
    t_lib.alignment = WD_TABLE_ALIGNMENT.CENTER
    lib_headers = ["Tên gói thư viện", "Phiên bản", "Mục đích sử dụng trong hệ thống"]
    for i, h in enumerate(lib_headers):
        cell = t_lib.rows[0].cells[i]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    lib_data = [
        ("fastapi", ">=0.109.0", "Web framework bất đồng bộ, xử lý routing, API endpoints và phân quyền."),
        ("uvicorn[standard]", ">=0.27.0", "Web server ASGI chạy ứng dụng FastAPI đa luồng."),
        ("sqlalchemy", ">=2.0.25", "ORM quản lý CSDL SQLite, định nghĩa models, transaction chống trùng lịch."),
        ("pydantic / pydantic-settings", ">=2.6.0", "Kiểm tra kiểu dữ liệu đầu vào và nạp cấu hình hệ thống từ file .env."),
        ("passlib[bcrypt]", ">=1.7.4", "Băm mật khẩu người dùng chuẩn mã hóa bcrypt an toàn."),
        ("python-jose[cryptography]", ">=3.3.0", "Tạo và giải mã JWT token phục vụ xác thực người dùng."),
        ("python-multipart", ">=0.0.9", "Phân tích cú pháp form dữ liệu gửi từ giao diện web (Login, Booking form)."),
        ("jinja2", ">=3.1.3", "Kết xuất giao diện HTML động phía máy chủ kết hợp Bootstrap."),
        ("google-generativeai", ">=0.4.0", "Giao tiếp với mô hình Gemini AI cho các tính năng thông minh."),
        ("pytest / httpx", ">=8.0.0", "Chạy các bộ kiểm thử tự động cho toàn bộ API và logic nghiệp vụ."),
        ("aiofiles", ">=23.2.1", "Đọc ghi file bất đồng bộ (hình ảnh, tài liệu tĩnh).")
    ]
    for r_idx, (name, ver, purpose) in enumerate(lib_data, start=1):
        row = t_lib.rows[r_idx]
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate([name, ver, purpose]):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            if c_idx == 0:
                r.font.name = "Consolas"
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 5. CÁC BƯỚC CÀI ĐẶT
    add_sec_heading("5. CÁC BƯỚC CÀI ĐẶT VÀ KHỞI CHẠY CHƯƠNG TRÌNH")
    
    add_p("Cách 1: Khởi động 1-Click bằng file run.bat (Khuyên dùng trên Windows)", bold_prefix="⭐ ")
    add_p("Đây là cách tiện lợi nhất cho Ban Giám Khảo và Giảng viên chấm thi. File run.bat đã được lập trình sẵn kịch bản tự động:")
    add_p("1. Mở thư mục 03_Chuong_Trinh_Thu_Nghiem trên đĩa CD (hoặc copy thư mục ra ổ C/D của máy).")
    add_p("2. Nhấp đúp chuột (Double Click) vào file run.bat.")
    add_p("3. Kịch bản sẽ tự động chạy 3 bước:")
    add_p("   • Bước 1: Tự động kiểm tra Python và cài đặt các thư viện thiếu qua pip.")
    add_p("   • Bước 2: Tự động khởi tạo và nạp dữ liệu mẫu ban đầu (app.seed_data).")
    add_p("   • Bước 3: Khởi động máy chủ Web Server FastAPI tại cổng 8000.")
    add_p("4. Mở trình duyệt web bất kỳ và truy cập địa chỉ: http://127.0.0.1:8000")

    add_p("Cách 2: Cài đặt và chạy thủ công qua Terminal / VS Code", bold_prefix="💻 ")
    add_p("Nếu muốn chạy thủ công từng bước trong môi trường lập trình (VS Code, PowerShell, CMD), thực hiện lần lượt các lệnh sau:")

    add_p("Bước 1: Mở Terminal tại thư mục mã nguồn và tạo môi trường ảo Python (khuyên dùng):")
    add_code_block("python -m venv .venv\n.venv\\Scripts\\activate    # Trên Windows (cmd/PowerShell)\n# source .venv/bin/activate  # Trên macOS/Linux")

    add_p("Bước 2: Cài đặt các gói thư viện cần thiết:")
    add_code_block("pip install -r requirements.txt")

    add_p("Bước 3: Khởi tạo cơ sở dữ liệu mẫu ban đầu:")
    add_code_block("python -m app.seed_data")

    add_p("Bước 4: Khởi động máy chủ FastAPI:")
    add_code_block("uvicorn app.main:app --reload --port 8000 --host 0.0.0.0")

    add_p("Bước 5: Truy cập hệ thống trên trình duyệt:")
    add_p("• Trang chủ ứng dụng Web: http://127.0.0.1:8000")
    add_p("• Tài liệu tương tác API Swagger UI: http://127.0.0.1:8000/docs")

    # 6. TÀI KHOẢN MẪU
    add_sec_heading("6. TÀI KHOẢN ĐĂNG NHẬP THỬ NGHIỆM")
    add_p("Hệ thống đã chuẩn bị sẵn 3 tài khoản tương ứng với 3 vai trò phân quyền. Người dùng có thể nhập trực tiếp hoặc nhấn nút Đăng nhập nhanh 1 chạm trên giao diện:")

    t_acc = doc.add_table(rows=4, cols=4)
    t_acc.alignment = WD_TABLE_ALIGNMENT.CENTER
    acc_headers = ["Vai trò", "Tên đăng nhập", "Mật khẩu", "Quyền hạn chính"]
    for i, h in enumerate(acc_headers):
        cell = t_acc.rows[0].cells[i]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    acc_data = [
        ("Admin (Quản trị viên)", "admin", "admin123", "Toàn quyền quản lý sân, bảng giá, xem báo cáo doanh thu & gợi ý chiến lược AI."),
        ("Nhân viên (Lễ tân)", "nhanvien", "staff123", "Tạo đơn đặt sân, thu cọc, đổi/hủy lịch, sinh tin nhắn thông báo AI gửi khách."),
        ("Khách hàng", "khachhang", "user123", "Tra cứu sân trống, nhờ AI tư vấn giờ, đặt sân và xem lịch sử đơn cá nhân.")
    ]
    for r_idx, row_values in enumerate(acc_data, start=1):
        row = t_acc.rows[r_idx]
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_values):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10.5)
            if c_idx in (1, 2):
                r.font.name = "Consolas"
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 7. CHẠY KIỂM THỬ PYTEST
    add_sec_heading("7. CHẠY KIỂM THỬ TỰ ĐỘNG (AUTOMATED TESTING)")
    add_p("Hệ thống đi kèm bộ kiểm thử tự động với Pytest kiểm tra toàn diện các kịch bản nghiệp vụ khắt khe nhất (như chống trùng lịch, phân quyền, AI Service).")
    add_p("Để thực thi kiểm thử, chạy lệnh sau trong Terminal:")
    add_code_block("pytest -v")
    add_p("Kết quả kỳ vọng: Toàn bộ các bài kiểm thử đều đạt trạng thái PASSED.")

    # 8. XỬ LÝ SỰ CỐ
    add_sec_heading("8. XỬ LÝ SỰ CỐ VÀ CÁC CÂU HỎI THƯỜNG GẶP (TROUBLESHOOTING)")
    add_p("1. Lỗi cổng 8000 bị chiếm dụng (Port already in use):")
    add_p("   Khởi chạy server với cổng khác bằng cách thêm tham số --port 8080 (ví dụ: uvicorn app.main:app --port 8080).")
    add_p("2. Máy tính không có Internet hoặc chưa có API Key AI:")
    add_p("   Hệ thống đã tích hợp sẵn cơ chế Heuristic AI Fallback Mode. Ứng dụng sẽ tự động chuyển sang bộ thuật toán dự phòng thông minh trong code, đảm bảo vẫn gợi ý giờ và sinh tin nhắn chính xác mà không báo lỗi gián đoạn.")
    add_p("3. Lỗi lệnh 'python' không nhận diện (is not recognized):")
    add_p("   Đảm bảo khi cài đặt Python đã tích chọn 'Add Python to PATH', hoặc sử dụng đường dẫn đầy đủ của python.exe.")

    doc.save(output_path)
    print(f"Installation Guide DOCX generated at: {output_path}")

def create_installation_guide_md(output_path):
    md_content = """# 📖 HƯỚNG DẪN CÀI ĐẶT VÀ VẬN HÀNH CHƯƠNG TRÌNH THỬ NGHIỆM

> **BỘ GIÁO DỤC VÀ ĐÀO TẠO — TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG (ICTU)**  
> **HỌC PHẦN:** Ứng dụng Trí tuệ Nhân tạo (AIA331)  
> **ĐỀ TÀI:** HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CHO THUÊ TÍCH HỢP AI  
> **NHÓM THỰC HIỆN:** NHÓM 03 — LỚP: CNTT K23M  
> **GIẢNG VIÊN HƯỚNG DẪN:** ThS. Ngô Hữu Huy  
> **THÀNH VIÊN:**  
> 1. Nông Thành Chung (Nhóm trưởng)  
> 2. Nguyễn Văn Lộc  
> 3. Hoàng Trí Tường  

---

## 1. 📌 Tổng Quan Hệ Thống
Hệ thống là giải pháp web app toàn diện quản lý hoạt động cho thuê sân bóng đá, cầu lông, pickleball và tennis.
- **Cơ chế chống trùng lịch (Conflict Prevention):** Ngăn chặn 100% tình trạng 2 khách đặt trùng một khung giờ nhờ Database Transaction Lock.
- **3 Tính năng AI nổi bật:**
  1. **AI Gợi ý khung giờ còn trống:** Hiểu yêu cầu tự nhiên của khách (ngày, giờ, số người) và đối chiếu chính xác với các slot trống thực tế trong CSDL SQLite.
  2. **AI Sinh tin nhắn xác nhận & nhắc lịch:** Tự động sinh nội dung SMS ngắn gọn, Zalo OA thân thiện, Email trang trọng chỉ với 1 chạm.
  3. **AI Tóm tắt công suất & Gợi ý khuyến mãi:** Phân tích tỷ lệ lấp đầy giờ cao điểm/thấp điểm và đề xuất chiến dịch voucher kích cầu giờ vắng khách.
- **Chế độ AI Fallback Mode:** Tự động chuyển đổi sang giải thuật Rule-based thông minh khi mất mạng hoặc không có API Key, đảm bảo hệ thống không bao giờ bị dừng hoạt động trong các buổi chấm điểm.

---

## 2. 💻 Yêu Cầu Cấu Hình Hệ Thống

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
|---|---|---|
| **Hệ điều hành** | Windows 10 / Linux / macOS | Windows 10/11 (64-bit) |
| **Python** | Python 3.10 trở lên | Python 3.11, 3.12 hoặc 3.13 |
| **Bộ nhớ RAM** | Tối thiểu 2 GB | 4 GB trở lên |
| **Dung lượng đĩa** | 300 MB trống | 1 GB SSD trống |
| **Trình duyệt** | Bất kỳ trình duyệt nào | Google Chrome, Microsoft Edge |

---

## 3. 📚 Nguồn Tài Liệu Tham Khảo Chính Thống

1. **FastAPI Documentation:** Tài liệu chuẩn quốc tế về framework web RESTful API tốc độ cao.  
   👉 [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
2. **Uvicorn ASGI Server:** Tài liệu máy chủ web chạy ứng dụng bất đồng bộ.  
   👉 [https://www.uvicorn.org/](https://www.uvicorn.org/)
3. **SQLAlchemy 2.0 ORM:** Tài liệu ánh xạ dữ liệu và quản lý giao dịch CSDL ACID.  
   👉 [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
4. **OpenAI API & Prompt Engineering Guide:** Hướng dẫn thiết kế câu lệnh AI có cấu trúc cho LLM.  
   👉 [https://platform.openai.com/docs/](https://platform.openai.com/docs/)
5. **Google Generative AI Python SDK:** Tài liệu giao tiếp mô hình ngôn ngữ lớn Gemini.  
   👉 [https://ai.google.dev/](https://ai.google.dev/)
6. **Jinja2 Template Designer:** Hướng dẫn kết xuất template HTML phía máy chủ.  
   👉 [https://jinja.palletsprojects.com/](https://jinja.palletsprojects.com/)
7. **Bootstrap 5 Framework:** Bộ công cụ giao diện người dùng Responsive hiện đại.  
   👉 [https://getbootstrap.com/](https://getbootstrap.com/)
8. **Pytest Testing Framework:** Bộ công cụ kiểm thử tự động toàn diện.  
   👉 [https://docs.pytest.org/](https://docs.pytest.org/)
9. **Pydantic Data Validation:** Thư viện xác thực schema và dữ liệu đầu vào.  
   👉 [https://docs.pydantic.dev/](https://docs.pydantic.dev/)

---

## 4. 📦 Chi Tiết Các Gói Thư Viện Cần Cài Đặt (`requirements.txt`)

```text
fastapi>=0.109.0            # Web framework backend chính, xử lý API & routing
uvicorn[standard]>=0.27.0   # Web server ASGI đa luồng cho FastAPI
sqlalchemy>=2.0.25          # ORM làm việc với CSDL SQLite, quản lý Transaction
pydantic>=2.6.0             # Kiểm tra và xác thực dữ liệu đầu vào/ra
pydantic-settings>=2.1.0    # Đọc cấu hình từ file môi trường .env
passlib[bcrypt]>=1.7.4      # Mã hóa băm mật khẩu tài khoản người dùng
python-jose[cryptography]>=3.3.0 # Sinh và giải mã Token JWT xác thực phiên làm việc
python-multipart>=0.0.9     # Hỗ trợ nhận dữ liệu từ Form HTML POST
jinja2>=3.1.3               # Động cơ render trang HTML giao diện
google-generativeai>=0.4.0  # Kết nối mô hình Google Gemini AI
pytest>=8.0.0               # Thư viện kiểm thử tự động hệ thống
httpx>=0.26.0               # HTTP client bất đồng bộ phục vụ test API
aiofiles>=23.2.1            # Đọc ghi file tĩnh bất đồng bộ
```

---

## 5. 🚀 Các Bước Cài Đặt Và Khởi Chạy Chương Trình

### Cách 1: Chạy tự động 1-Click bằng file `run.bat` (Khuyên dùng)
1. Mở thư mục `03_Chuong_Trinh_Thu_Nghiem`.
2. Nhấp đúp chuột vào file **`run.bat`**.
3. Kịch bản sẽ tự động thực thi:
   - Tự cài đặt các thư viện thiếu trong `requirements.txt`.
   - Tự khởi tạo và nạp dữ liệu mẫu ban đầu (`python -m app.seed_data`).
   - Khởi động web server FastAPI tại cổng 8000.
4. Mở trình duyệt web truy cập:
   - **Giao diện Dashboard:** `http://127.0.0.1:8000`
   - **Tài liệu API Swagger:** `http://127.0.0.1:8000/docs`

---

### Cách 2: Cài đặt và chạy thủ công qua Terminal / VS Code

**Bước 1: Mở Terminal tại thư mục mã nguồn và tạo môi trường ảo (tùy chọn nhưng khuyên dùng):**
```bash
python -m venv .venv
.venv\\Scripts\\activate    # Trên Windows
```

**Bước 2: Cài đặt các gói thư viện phụ thuộc:**
```bash
pip install -r requirements.txt
```

**Bước 3: Khởi tạo cơ sở dữ liệu mẫu:**
```bash
python -m app.seed_data
```

**Bước 4: Khởi động máy chủ ứng dụng:**
```bash
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

**Bước 5: Mở trình duyệt web:**
Truy cập địa chỉ: `http://127.0.0.1:8000`

---

## 6. 🔑 Danh Sách Tài Khoản Đăng Nhập Mẫu

*(Ghi chú: Trên giao diện web đã có sẵn nút đăng nhập nhanh 1 chạm cho cả 3 vai trò)*

| Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn chính |
|---|---|---|---|
| **Admin (Quản trị viên)** | `admin` | `admin123` | Toàn quyền cấu hình sân, giá giờ vàng, xem doanh thu & đề xuất voucher AI |
| **Nhân viên (Lễ tân)** | `nhanvien` | `staff123` | Đặt sân tại quầy, thu tiền cọc, đổi/hủy lịch, sinh tin nhắn AI gửi khách |
| **Khách hàng** | `khachhang` | `user123` | Tra cứu sân trống, nhờ AI tư vấn giờ đá, đặt sân trực tuyến |

---

## 7. 🧪 Chạy Kiểm Thử Tự Động (Automated Testing)

Để kiểm tra độ tin cậy của mã nguồn và thuật toán chống trùng lịch:
```bash
pytest -v
```
Toàn bộ các test cases sẽ chạy và báo kết quả `PASSED`.

---

## 8. 🛠️ Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **Lỗi cổng 8000 bị chiếm dụng:**
   Chạy với cổng khác bằng lệnh:
   ```bash
   uvicorn app.main:app --port 8080
   ```
2. **Không có kết nối Internet hoặc chưa có API Key:**
   Hệ thống có sẵn chế độ **AI Fallback Heuristic** tự động xử lý nội bộ, đảm bảo mọi chức năng AI vẫn hoạt động trơn tru không xảy ra lỗi.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Installation Guide MD generated at: {output_path}")

if __name__ == "__main__":
    create_installation_guide_docx("g:/Du_An_San_The_Thao/test_guide.docx")
    create_installation_guide_md("g:/Du_An_San_The_Thao/test_guide.md")
