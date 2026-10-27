import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth_router, pitch_router, booking_router, payment_router,
    maintenance_router, stats_router, ai_router, community_router,
    wallet_router, customer_router, reports_router
)
from app.routers.pitch_router import courts_router, court_types_router
from app.routers.booking_router import timeslots_router
from app.routers.maintenance_router import maintenance_alias

# Khoi tao bang CSDL
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Hệ thống Quản Lý Sân Thể Thao Cho Thuê Tích Hợp Trí Tuệ Nhân Tạo (AI) - Học phần AIA331 ICTU - Nhóm 03",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount thu muc static va template
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Dang ky cac Routers API
app.include_router(auth_router.router)
app.include_router(pitch_router.router)
app.include_router(booking_router.router)
app.include_router(payment_router.router)
app.include_router(maintenance_router.router)
app.include_router(stats_router.router)
app.include_router(ai_router.router)
app.include_router(community_router.router)
app.include_router(wallet_router.router)
app.include_router(customer_router.router)
app.include_router(reports_router.router)
app.include_router(courts_router)
app.include_router(court_types_router)
app.include_router(timeslots_router)
app.include_router(maintenance_alias)

@app.get("/")
def render_homepage(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"project_name": settings.PROJECT_NAME}
    )

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "ai_engine": "Google Gemini & Smart Fallback",
        "project_team": "Nhóm 03 - Nông Thành Chung (Nhóm Trưởng), Nguyễn Văn Lộc, Hoàng Trí Tường",
        "version": "2.0.0"
    }

@app.get("/favicon.ico")
def get_favicon():
    return Response(content='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🏟️</text></svg>', media_type="image/svg+xml")
