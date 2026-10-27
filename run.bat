@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0" || goto :error

where python > nul 2>&1 || (
	echo Python was not found. Install Python and add it to PATH.
	goto :error
)
echo ==============================================================================
echo   HE THONG QUAN LY SAN THE THAO REN LUYEN THE HINH TRE ZHANH CHUNG (AI)
echo ==============================================================================
echo [1/3] Kiem tra va cai dat thu vien...
python -m pip install -r requirements.txt || goto :error
echo.
echo [2/3] Khoi tao co so du lieu mau (Seed Data)...
python -m app.seed_data || goto :error
echo.
echo [3/3] Khoi dong Web Server FastAPI...
echo Web Dashboard: http://127.0.0.1:8000
echo Swagger API:   http://127.0.0.1:8000/docs
echo ==============================================================================
python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 || goto :error
pause
exit /b 0

:error
echo.
echo Startup failed. Check the error message above.
pause
exit /b 1
