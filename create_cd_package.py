# -*- coding: utf-8 -*-
"""
Script to build the full CD Package for Group 03:
HỆ THỐNG QUẢN LÝ SÂN THỂ THAO CHO THUÊ TÍCH HỢP AI
"""
import os
import shutil
import math
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import pptx
from pptx.util import Inches as PInches, Pt as PPt
from pptx.dml.color import RGBColor as PRGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ROOT_DIR = Path("g:/Du_An_San_The_Thao")
CD_DIR = ROOT_DIR / "DIA_CD_NHOM_03"

def make_dirs():
    dirs = [
        CD_DIR / "01_Bao_Cao",
        CD_DIR / "02_Slide_Bao_Cao",
        CD_DIR / "03_Chuong_Trinh_Thu_Nghiem",
        CD_DIR / "04_Huong_Dan_Cai_Dat",
        CD_DIR / "05_Mau_Nhan_Dia_CD",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("Directories created successfully.")

def copy_report():
    src_report = ROOT_DIR / "NHÓM 03_Nông Thành Chung_2026,09mm,17.docx"
    dst_report = CD_DIR / "01_Bao_Cao" / "NHOM_03_Bao_Cao_He_Thong_Quan_Ly_San_The_Thao.docx"
    if src_report.exists():
        shutil.copy2(src_report, dst_report)
        print(f"Copied report to {dst_report}")
    else:
        print("Warning: Source report docx not found!")

def copy_clean_code():
    dst_code = CD_DIR / "03_Chuong_Trinh_Thu_Nghiem"
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
    print("Clean code copied successfully.")

if __name__ == "__main__":
    make_dirs()
    copy_report()
    copy_clean_code()
