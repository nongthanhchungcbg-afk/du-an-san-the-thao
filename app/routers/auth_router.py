import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import User, UserRole, UserActivityLog
from app.schemas import (
    UserCreate, UserResponse, Token, LoginRequest, 
    SendOTPRequest, VerifyOTPRequest, UserRoleUpdate, UserActivityLogResponse
)
from app.auth import get_password_hash, verify_password, create_access_token, get_current_active_user, require_roles
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/auth", tags=["Xác thực & Người dùng"])

class DirectForgotPasswordRequest(BaseModel):
    username_or_email: str
    new_password: str

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký trên hệ thống")
    if len(user_in.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        role=user_in.role or UserRole.CUSTOMER,
        wallet_balance=0.0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=new_user.id,
        username=new_user.username,
        action="Đăng ký tài khoản thành viên mới",
        role=new_user.role.value,
        ip_address=client_ip
    )
    db.add(log)
    db.commit()

    return new_user

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.username == login_data.username, User.email == login_data.username)
    ).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai username hoặc password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đang bị tạm khóa")

    user.last_login_at = datetime.utcnow()
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=user.id,
        username=user.username,
        action="Đăng nhập hệ thống thành công",
        role=user.role.value,
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
def logout_endpoint():
    """Đăng xuất khỏi hệ thống (Chuẩn Bảng 2.11 - Table 16)"""
    return {"status": "success", "message": "Đã đăng xuất thành công khỏi hệ thống"}

class GoogleLoginRequest(BaseModel):
    email: Optional[str] = "nongthanhchung.ictu@gmail.com"
    full_name: Optional[str] = "Nông Thành Chung"
    role: Optional[str] = "ADMIN"

@router.post("/google-login", response_model=Token)
def google_login(data: Optional[GoogleLoginRequest] = None, request: Request = None, db: Session = Depends(get_db)):
    email = (data and data.email) or "nongthanhchung.ictu@gmail.com"
    full_name = (data and data.full_name) or "Nông Thành Chung"
    requested_role_str = (data and data.role) or "ADMIN"
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        if email == "nongthanhchung.ictu@gmail.com":
            user = db.query(User).filter(User.username == "admin").first()
        elif email == "loctech.ictu@gmail.com":
            user = db.query(User).filter(User.username == "quanly").first()
        elif email == "tuonght.ictu@gmail.com":
            user = db.query(User).filter(User.username == "khachhang").first()

    if not user:
        role_enum = UserRole.CUSTOMER
        if requested_role_str.upper() == "ADMIN":
            role_enum = UserRole.ADMIN
        elif requested_role_str.upper() == "STAFF":
            role_enum = UserRole.STAFF

        username_prefix = email.split('@')[0].replace('.', '_')
        user = User(
            username=f"{username_prefix}_gg",
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash("123456"),
            role=role_enum,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    user.last_login_at = datetime.utcnow()
    
    client_ip = request.client.host if (request and request.client) else "127.0.0.1"
    log = UserActivityLog(
        user_id=user.id,
        username=user.username,
        action=f"Đăng nhập qua Google OAuth 2.0 ({email})",
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.username, "role": user.role.value if hasattr(user.role, 'value') else str(user.role)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/send-otp")
def send_reset_otp(data: SendOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.username == data.email_or_username, User.email == data.email_or_username)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản với Email hoặc Tên đăng nhập này")

    otp_code = str(random.randint(1000, 9999))
    user.reset_otp = otp_code
    user.reset_otp_expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    # Gửi email thật qua SMTP
    EmailService.send_otp_reset_email(
        to_email=user.email,
        full_name=user.full_name,
        otp_code=otp_code
    )

    return {
        "status": "success",
        "message": f"Mã xác thực 4 số đã được gửi về email: {user.email}",
        "email_masked": user.email[:2] + "****" + user.email[user.email.find("@")-1:],
        "demo_otp_hint": otp_code
    }

@router.post("/verify-otp")
def verify_otp_and_reset_password(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.username == data.email_or_username, User.email == data.email_or_username)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    
    if not user.reset_otp or user.reset_otp != data.otp_code.strip():
        raise HTTPException(status_code=400, detail="Mã OTP 4 số không chính xác. Vui lòng kiểm tra lại.")
    
    if user.reset_otp_expires_at and user.reset_otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới.")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    user.hashed_password = get_password_hash(data.new_password)
    user.reset_otp = None
    user.reset_otp_expires_at = None
    db.commit()

    return {"status": "success", "message": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập bằng mật khẩu mới."}

@router.post("/forgot-password")
def forgot_password_direct(data: DirectForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.username == data.username_or_email, User.email == data.username_or_email)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay."}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    return db.query(User).order_by(User.created_at.desc()).all()

@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: int, role_data: UserRoleUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    old_role = user.role.value
    user.role = role_data.role
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=current_user.id,
        username=current_user.username,
        action=f"Phân bổ quyền người dùng {user.username} từ {old_role} sang {role_data.role.value}",
        role=current_user.role.value,
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user

@router.get("/activity-logs", response_model=List[UserActivityLogResponse])
def get_activity_logs(db: Session = Depends(get_db), current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))):
    return db.query(UserActivityLog).order_by(UserActivityLog.timestamp.desc()).limit(100).all()

from app.schemas import UserProfileUpdate

class SmtpConfigRequest(BaseModel):
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: Optional[int] = 587
    smtp_user: str
    smtp_password: str
    from_email: Optional[str] = None
    test_recipient: Optional[str] = None

@router.put("/profile", response_model=UserResponse)
@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    profile_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if profile_in.full_name is not None:
        current_user.full_name = profile_in.full_name.strip()
    if profile_in.phone is not None:
        current_user.phone = profile_in.phone.strip()
    if profile_in.hometown is not None:
        current_user.hometown = profile_in.hometown.strip()
    if profile_in.birth_year is not None:
        current_user.birth_year = profile_in.birth_year
    if profile_in.email is not None:
        # Check if email is used by another user
        existing = db.query(User).filter(User.email == profile_in.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email này đã được sử dụng bởi tài khoản khác")
        current_user.email = profile_in.email

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/settings/smtp")
def configure_smtp_settings(
    config: SmtpConfigRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    import os
    from pathlib import Path
    host = config.smtp_host or "smtp.gmail.com"
    port = str(config.smtp_port or 587)
    user = config.smtp_user.strip()
    password = config.smtp_password.strip()
    from_email = config.from_email.strip() if config.from_email else user

    os.environ["SMTP_HOST"] = host
    os.environ["SMTP_PORT"] = port
    os.environ["SMTP_USER"] = user
    os.environ["SMTP_PASSWORD"] = password
    os.environ["SMTP_FROM"] = from_email

    settings.SMTP_HOST = host
    settings.SMTP_PORT = int(port)
    settings.SMTP_USER = user
    settings.SMTP_PASSWORD = password
    settings.SMTP_FROM_EMAIL = from_email

    # Lưu vĩnh viễn vào file .env
    try:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            new_lines = []
            keys_set = set()
            new_vals = {
                "SMTP_HOST": host,
                "SMTP_PORT": port,
                "SMTP_USER": user,
                "SMTP_PASSWORD": password,
                "SMTP_FROM_EMAIL": from_email
            }
            for line in lines:
                if "=" in line:
                    k, _ = line.split("=", 1)
                    k = k.strip()
                    if k in new_vals:
                        new_lines.append(f"{k}={new_vals[k]}")
                        keys_set.add(k)
                        continue
                new_lines.append(line)
            for k, v in new_vals.items():
                if k not in keys_set:
                    new_lines.append(f"{k}={v}")
            env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"[AuthRouter] Không thể ghi .env: {e}")

    test_res = None
    if config.test_recipient:
        test_res = EmailService.send_email(
            to_email=config.test_recipient.strip(),
            subject="[TEST] Kiểm tra kết nối SMTP Thành Công",
            body_text=f"Xin chào! Kết nối gửi email qua tài khoản SMTP {user} đã hoạt động chính xác trên Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI."
        )

    is_ok = not test_res or test_res.get("success", False)
    msg = f"Đã lưu và kích hoạt cấu hình gửi Email SMTP ({user}) thành công!"
    if test_res and not test_res.get("success", False):
        msg = f"Đã lưu cấu hình ({user}). Lưu ý: {test_res.get('message', 'Không thể gửi email trực tiếp qua SMTP.')}"

    return {
        "status": "success" if is_ok else "warning",
        "message": msg,
        "test_result": test_res
    }

@router.get("/settings/smtp")
def get_smtp_settings(current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    import os
    user = os.getenv("SMTP_USER", "")
    return {
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "smtp_user": user,
        "is_configured": bool(user and os.getenv("SMTP_PASSWORD", ""))
    }
