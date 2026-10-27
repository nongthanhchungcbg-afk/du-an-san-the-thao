# -*- coding: utf-8 -*-
"""
Generates the CD Label graphic, Word document, and HTML print template
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_cd_label_image(output_path):
    # Standard CD size: 118mm ~ 4.65 inches. We render at 300 DPI -> 1400x1400 px
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300)
    fig.patch.set_facecolor('white')

    # Coordinates: Center at (0.5, 0.5)
    # Outer circle: radius = 0.46
    outer_circle = patches.Circle(
        (0.5, 0.5), 0.46,
        facecolor='#DFEAFC', # Soft gentle pastel blue
        edgecolor='#2563EB', # Vibrant blue line
        linewidth=2.5,
        zorder=1
    )
    ax.add_patch(outer_circle)

    # Subtle inner concentric ring for aesthetic depth
    outer_guide = patches.Circle(
        (0.5, 0.5), 0.43,
        facecolor='none',
        edgecolor='#93C5FD',
        linewidth=0.8,
        linestyle='--',
        zorder=2
    )
    ax.add_patch(outer_guide)

    # Center hole: radius = 0.12 (standard 22mm hole)
    center_hole = patches.Circle(
        (0.5, 0.5), 0.11,
        facecolor='white',
        edgecolor='#2563EB',
        linewidth=2.0,
        zorder=3
    )
    ax.add_patch(center_hole)

    # Center plastic rim guide
    inner_rim = patches.Circle(
        (0.5, 0.5), 0.15,
        facecolor='none',
        edgecolor='#BFDBFE',
        linewidth=0.8,
        linestyle=':',
        zorder=2
    )
    ax.add_patch(inner_rim)

    # Text Upper Section (Centered above inner hole)
    ax.text(0.5, 0.77, "NHÓM 03:",
            fontsize=16, fontweight='bold', fontfamily='sans-serif',
            color='#0F172A', ha='center', va='center', zorder=4)

    ax.text(0.5, 0.70, "HỆ THỐNG QUẢN LÝ SÂN THỂ THAO",
            fontsize=13, fontweight='bold', fontfamily='sans-serif',
            color='#0F172A', ha='center', va='center', zorder=4)

    ax.text(0.5, 0.65, "CHO THUÊ TÍCH HỢP AI",
            fontsize=13, fontweight='bold', fontfamily='sans-serif',
            color='#0F172A', ha='center', va='center', zorder=4)

    # Text Lower Section (Centered below inner hole)
    ax.text(0.5, 0.33, "Học phần: Ứng dụng Trí tuệ nhân tạo",
            fontsize=13, fontweight='normal', fontfamily='sans-serif',
            color='#0F172A', ha='center', va='center', zorder=4)

    ax.text(0.5, 0.25, "Lớp: CNTT K23M",
            fontsize=13, fontweight='normal', fontfamily='sans-serif',
            color='#0F172A', ha='center', va='center', zorder=4)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.savefig(output_path, bbox_inches='tight', pad_inches=0.05, dpi=300)
    plt.close()
    print(f"CD Label PNG image saved at: {output_path}")

def generate_cd_label_docx(image_path, output_docx_path):
    doc = docx.Document()
    
    # Margins: 1.5 cm all sides
    for s in doc.sections:
        s.top_margin = Inches(0.6)
        s.bottom_margin = Inches(0.6)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("MẪU IN NHÃN ĐĨA CD ĐỒ ÁN / TIỂU LUẬN CHUẨN")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(14)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(30, 58, 138)
    p_title.paragraph_format.space_after = Pt(2)

    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_guide = p_guide.add_run("• Kích thước in chuẩn đường kính: 11.8 cm (118 mm) | Lỗ tâm chuẩn: 2.2 cm\n• Hướng dẫn: Đặt giấy Decal in đĩa CD/DVD vào máy in -> Bấm Ctrl + P -> Chọn kích cỡ 100% (Actual Size)")
    r_guide.font.name = "Times New Roman"
    r_guide.font.size = Pt(10)
    r_guide.font.italic = True
    r_guide.font.color.rgb = RGBColor(100, 116, 139)
    p_guide.paragraph_format.space_after = Pt(14)

    # Center table to hold the image
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    p_cell = cell.paragraphs[0]
    p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 11.8 cm = 4.645 inches
    p_cell.add_run().add_picture(str(image_path), width=Inches(4.65), height=Inches(4.65))
    p_cell.paragraph_format.space_after = Pt(8)

    p_footer = doc.add_paragraph()
    p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_foot = p_footer.add_run("NHÓM 03: Nông Thành Chung - Nguyễn Văn Lộc - Hoàng Trí Tường | GVHD: ThS. Ngô Hữu Huy")
    r_foot.font.name = "Times New Roman"
    r_foot.font.size = Pt(10.5)
    r_foot.font.bold = True
    r_foot.font.color.rgb = RGBColor(30, 58, 138)

    doc.save(output_docx_path)
    print(f"CD Label DOCX saved at: {output_docx_path}")

def generate_cd_label_html(output_html_path):
    html_content = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mẫu Nhãn Đĩa CD - Nhóm 03</title>
    <style>
        @page {
            size: A4;
            margin: 15mm;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f1f5f9;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .instructions {
            max-width: 600px;
            text-align: center;
            margin-bottom: 25px;
            background: white;
            padding: 15px 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .instructions h2 {
            margin: 0 0 8px 0;
            color: #1e3a8a;
            font-size: 18px;
        }
        .instructions p {
            margin: 4px 0;
            color: #475569;
            font-size: 13px;
        }
        .btn-print {
            margin-top: 10px;
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
        }
        .btn-print:hover {
            background-color: #1d4ed8;
        }
        /* Exact CD Label 118mm x 118mm */
        .cd-disc {
            width: 118mm;
            height: 118mm;
            border-radius: 50%;
            background: radial-gradient(circle, #eef5fc 0%, #dfeafc 75%, #cfdff9 100%);
            border: 2.5px solid #2563eb;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            box-sizing: border-box;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
            page-break-inside: avoid;
        }
        .cd-inner-ring {
            position: absolute;
            width: 110mm;
            height: 110mm;
            border-radius: 50%;
            border: 1px dashed rgba(37, 99, 235, 0.35);
            pointer-events: none;
        }
        .cd-center-hole {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 22mm;
            height: 22mm;
            border-radius: 50%;
            background-color: white;
            border: 2px solid #2563eb;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);
        }
        .cd-text-top {
            margin-top: 14mm;
            text-align: center;
            z-index: 2;
        }
        .cd-group {
            font-size: 15pt;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
            letter-spacing: 0.5px;
        }
        .cd-title {
            font-size: 11.5pt;
            font-weight: 800;
            color: #0f172a;
            margin: 4px 0 0 0;
            line-height: 1.3;
        }
        .cd-text-bottom {
            margin-bottom: 15mm;
            text-align: center;
            z-index: 2;
        }
        .cd-course {
            font-size: 11pt;
            color: #0f172a;
            margin: 0;
            font-weight: 600;
        }
        .cd-class {
            font-size: 11pt;
            color: #0f172a;
            margin: 3px 0 0 0;
            font-weight: 600;
        }
        @media print {
            body {
                background: white;
                padding: 0;
            }
            .instructions {
                display: none;
            }
            .cd-disc {
                box-shadow: none;
            }
        }
    </style>
</head>
<body>
    <div class="instructions">
        <h2>🏷️ MẪU IN NHÃN ĐĨA CD - NHÓM 03 (ICTU)</h2>
        <p>Kích thước chuẩn: Đường kính ngoài <b>118mm</b> | Lỗ trong <b>22mm</b></p>
        <p>Bấm nút bên dưới để in trực tiếp lên giấy Decal dán đĩa CD (Khổ in A4, tỉ lệ 100%):</p>
        <button class="btn-print" onclick="window.print()">🖨️ In Nhãn Đĩa Ngay (Ctrl + P)</button>
    </div>

    <div class="cd-disc">
        <div class="cd-inner-ring"></div>
        <div class="cd-text-top">
            <h1 class="cd-group">NHÓM 03:</h1>
            <h2 class="cd-title">HỆ THỐNG QUẢN LÝ SÂN THỂ THAO<br>CHO THUÊ TÍCH HỢP AI</h2>
        </div>
        <div class="cd-center-hole"></div>
        <div class="cd-text-bottom">
            <p class="cd-course">Học phần: Ứng dụng Trí tuệ nhân tạo</p>
            <p class="cd-class">Lớp: CNTT K23M</p>
        </div>
    </div>
</body>
</html>
"""
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"CD Label HTML template saved at: {output_html_path}")

if __name__ == "__main__":
    generate_cd_label_image("g:/Du_An_San_The_Thao/test_cd.png")
    generate_cd_label_docx("g:/Du_An_San_The_Thao/test_cd.png", "g:/Du_An_San_The_Thao/test_cd.docx")
    generate_cd_label_html("g:/Du_An_San_The_Thao/test_cd.html")
