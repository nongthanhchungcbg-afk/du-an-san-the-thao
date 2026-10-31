@echo off
chcp 65001 >nul
title TRUY VAN CO SO DU LIEU SQLITE - SAN THE THAO
echo Dang thuc hien truy van CSDL sports_pitch.db...
echo.
python query_db.py
echo.
pause

