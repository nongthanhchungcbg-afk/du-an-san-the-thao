import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hệ Thống Quản Lý Sân Thể Thao Cho Thuê Tích Hợp AI - Nhóm 03"
    SECRET_KEY: str = "super-secret-jwt-key-pitch-ai-management-2026-ictu-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    DATABASE_URL: str = "sqlite:///./sports_pitch.db"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    AI_FALLBACK_MODE: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # SMTP Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@santhethaoictu.vn"
    SMTP_FROM_NAME: str = "Hệ Thống Sân Thể Thao Tích Hợp AI (Nhóm 03)"
    SMTP_TLS: bool = True


    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
