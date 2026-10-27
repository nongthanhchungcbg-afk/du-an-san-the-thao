# -*- coding: utf-8 -*-
"""
Master script to assemble the entire CD package for Group 03
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import shutil
from pathlib import Path
from generate_presentation import create_presentation
from generate_installation_guide import create_installation_guide_docx, create_installation_guide_md
from generate_cd_label import generate_cd_label_image, generate_cd_label_docx, generate_cd_label_html

ROOT_DIR = Path("g:/Du_An_San_The_Thao")
CD_DIR = ROOT_DIR / "DIA_CD_NHOM_03"

def build():
    print("=" * 70)
    print("BẮT ĐẦU ĐÓNG GÓI TOÀN BỘ NỘI DUNG ĐĨA CD - NHÓM 03")
    print("=" * 70)

    # 1. Tạo các thư mục con theo cấu trúc chuẩn mực
    dirs = {
        "report": CD_DIR / "01_Bao_Cao",
        "slide": CD_DIR / "02_Slide_Bao_Cao",
        "code": CD_DIR / "03_Chuong_Trinh_Thu_Nghiem",
        "guide": CD_DIR / "04_Huong_Dan_Cai_Dat",
        "label": CD_DIR / "05_Mau_Nhan_Dia_CD",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    print("[1/6] Đã khởi tạo cấu trúc thư mục đĩa CD.")

    # 2. Thư mục 01_Bao_Cao: Copy file Word báo cáo chính thức
    src_docx = ROOT_DIR / "NHÓM 03_Nông Thành Chung_2026,09mm,17.docx"
    dst_docx = dirs["report"] / "NHOM_03_Bao_Cao_He_Thong_Quan_Ly_San_The_Thao.docx"
    if src_docx.exists():
        shutil.copy2(src_docx, dst_docx)
        print(f"[2/6] Đã sao chép Báo cáo Word vào: {dst_docx.name}")
    else:
        print("[2/6] ⚠️ Không tìm thấy file báo cáo Word gốc!")

    # 3. Thư mục 02_Slide_Bao_Cao: Tạo file trình chiếu PowerPoint
    dst_slide = dirs["slide"] / "NHOM_03_Slide_Thuyet_Trinh_He_Thong_Quan_Ly_San_The_Thao_AI.pptx"
    create_presentation(str(dst_slide))
    print(f"[3/6] Đã tạo Slide PowerPoint 18 trang tại: {dst_slide.name}")

    # 4. Thư mục 03_Chuong_Trinh_Thu_Nghiem: Sao chép toàn bộ mã nguồn sạch
    dst_code = dirs["code"]
    items_to_copy = [
        "app",
        "templates",
        "static",
        "tests",
        "docs",
        "sports_pitch.db",
        "requirements.txt",
        "run.bat",
        ".env.example",
        "Dockerfile",
        "README.md",
    ]
    ignore_patterns = shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".pytest_cache", ".venv", "*.log", ".git"
    )
    for item in items_to_copy:
        src = ROOT_DIR / item
        dst = dst_code / item
        if not src.exists():
            continue
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=ignore_patterns)
        else:
            shutil.copy2(src, dst)
    print(f"[4/6] Đã sao chép toàn bộ mã nguồn chương trình thử nghiệm (Codes) sạch.")

    # 5. Thư mục 04_Huong_Dan_Cai_Dat: Tạo Hướng dẫn cài đặt DOCX & MD + file run.bat phụ
    dst_guide_docx = dirs["guide"] / "HUONG_DAN_CAI_DAT_CHUONG_TRINH_THU_NGHIEM.docx"
    dst_guide_md = dirs["guide"] / "HUONG_DAN_CAI_DAT_CHUONG_TRINH_THU_NGHIEM.md"
    create_installation_guide_docx(str(dst_guide_docx))
    create_installation_guide_md(str(dst_guide_md))
    shutil.copy2(ROOT_DIR / "run.bat", dirs["guide"] / "run.bat")
    print(f"[5/6] Đã tạo Hướng dẫn cài đặt (Word + Markdown) và file chạy nhanh run.bat.")

    # 6. Thư mục 05_Mau_Nhan_Dia_CD: Tạo nhãn đĩa tròn PNG, Word và HTML
    dst_cd_img = dirs["label"] / "Nhan_Dia_CD_Nhom_03.png"
    dst_cd_docx = dirs["label"] / "Mau_In_Nhan_Dia_CD.docx"
    dst_cd_html = dirs["label"] / "Nhan_Dia_CD_Nhom_03.html"
    generate_cd_label_image(str(dst_cd_img))
    generate_cd_label_docx(str(dst_cd_img), str(dst_cd_docx))
    generate_cd_label_html(str(dst_cd_html))
    print(f"[6/6] Đã tạo Mẫu nhãn đĩa CD (File in Word, Ảnh PNG 300DPI, Giao diện HTML).")

    # 7. Tạo file README_DIA_CD.txt ở thư mục gốc đĩa CD
    readme_content = """================================================================================
                    NỘI DUNG ĐĨA CD BÁO CÁO TIỂU LUẬN / ĐỒ ÁN
================================================================================
HỌC PHẦN: ỨNG DỤNG TRÍ TUỆ NHÂN TẠO (AIA331)
ĐỀ TÀI:   HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CHO THUÊ TÍCH HỢP AI
NHÓM:     NHÓM 03
LỚP:      CNTT K23M
TRƯỜNG:   ĐẠI HỌC CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG (ICTU)
GIẢNG VIÊN HƯỚNG DẪN: ThS. NGÔ HỮU HUY

THÀNH VIÊN THỰC HIỆN:
  1. Nông Thành Chung (Nhóm trưởng)
  2. Nguyễn Văn Lộc
  3. Hoàng Trí Tường
================================================================================

CẤU TRÚC THƯ MỤC TRÊN ĐĨA CD:
--------------------------------------------------------------------------------
📁 01_Bao_Cao/
   └── NHOM_03_Bao_Cao_He_Thong_Quan_Ly_San_The_Thao.docx
       -> Toàn bộ nội dung quyển báo cáo tiểu luận định dạng Microsoft Word.

📁 02_Slide_Bao_Cao/
   └── NHOM_03_Slide_Thuyet_Trinh_He_Thong_Quan_Ly_San_The_Thao_AI.pptx
       -> 18 slide thuyết trình chuẩn 16:9 hiện đại, tóm tắt toàn diện đề tài,
          kiến trúc hệ thống, 3 chức năng AI, prompt engineering, kiểm thử.

📁 03_Chuong_Trinh_Thu_Nghiem/
   └── Toàn bộ mã nguồn chương trình thử nghiệm (Codes) hoàn chỉnh:
       ├── app/ (Backend FastAPI, Models, Routers, AI Services, Prompts)
       ├── templates/ (Giao diện HTML Jinja2 Responsive)
       ├── static/ (CSS, JavaScript, Icons, Images)
       ├── tests/ (Bộ kiểm thử tự động Pytest)
       ├── sports_pitch.db (Cơ sở dữ liệu mẫu SQLite đã nạp sẵn dữ liệu)
       ├── requirements.txt (Danh sách thư viện phụ thuộc)
       └── run.bat (Kịch bản 1-Click tự động chạy server trên Windows)

📁 04_Huong_Dan_Cai_Dat/
   ├── HUONG_DAN_CAI_DAT_CHUONG_TRINH_THU_NGHIEM.docx (Định dạng Word chuyên nghiệp)
   ├── HUONG_DAN_CAI_DAT_CHUONG_TRINH_THU_NGHIEM.md   (Định dạng Markdown xem nhanh)
   └── run.bat (File khởi động nhanh)
       -> Chi tiết yêu cầu cấu hình phần cứng/phần mềm, nguồn tài liệu tham khảo,
          giải thích từng thư viện, các bước khởi chạy và tài khoản thử nghiệm.

📁 05_Mau_Nhan_Dia_CD/
   ├── Mau_In_Nhan_Dia_CD.docx (Khổ A4 chuẩn, chứa hình tròn 11.8cm, sẵn sàng in dán)
   ├── Nhan_Dia_CD_Nhom_03.png (Ảnh nhãn đĩa độ nét cao 300 DPI)
   └── Nhan_Dia_CD_Nhom_03.html (Mở bằng trình duyệt để xem và in trực tiếp)

--------------------------------------------------------------------------------
CÁCH CHẠY NHANH CHƯƠNG TRÌNH THỬ NGHIỆM TRÊN WINDOWS:
1. Mở thư mục "03_Chuong_Trinh_Thu_Nghiem" (hoặc copy ra máy tính).
2. Nhấp đúp chuột vào file "run.bat".
3. Mở trình duyệt web truy cập: http://127.0.0.1:8000
4. Tài khoản đăng nhập mẫu:
   - Quản trị viên: admin / admin123
   - Nhân viên lễ tân: nhanvien / staff123
   - Khách hàng: khachhang / user123
================================================================================
"""
    with open(CD_DIR / "README_DIA_CD.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("Đã tạo file README_DIA_CD.txt ở thư mục gốc đĩa.")

    # Dọn dẹp các file test tạm
    test_files = [
        ROOT_DIR / "test_presentation.pptx",
        ROOT_DIR / "test_guide.docx",
        ROOT_DIR / "test_guide.md",
        ROOT_DIR / "test_cd.png",
        ROOT_DIR / "test_cd.docx",
        ROOT_DIR / "test_cd.html",
    ]
    for tf in test_files:
        if tf.exists():
            tf.unlink()

    print("=" * 70)
    print("HOÀN TẤT ĐÓNG GÓI ĐĨA CD TẠI:")
    print(CD_DIR)
    print("=" * 70)

if __name__ == "__main__":
    build()
