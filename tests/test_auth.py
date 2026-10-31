from fastapi.testclient import TestClient
from app.main import app
from app.services.email_service import EmailService

client = TestClient(app)

def test_login_success():
    res = client.post("/api/auth/login", json={
        "username": "nongthanhchung",
        "password": "Admin"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMIN"

def test_login_wrong_password():
    res = client.post("/api/auth/login", json={
        "username": "nongthanhchung",
        "password": "sai_password"
    })
    assert res.status_code == 401

def test_forgot_password_otp_flow(monkeypatch):
    monkeypatch.setattr(EmailService, "send_otp_reset_email", lambda **kwargs: {
        "success": True,
        "mode": "LIVE_SMTP",
        "message": "Sent by test SMTP"
    })

    # 1. Send OTP 4 digits
    send_res = client.post("/api/auth/send-otp", json={
        "email_or_username": "hoangtrituong"
    })
    assert send_res.status_code == 200
    data = send_res.json()
    assert "demo_otp_hint" in data
    otp_code = data["demo_otp_hint"]
    assert len(otp_code) == 4

    # 2. Verify OTP & Reset Password
    verify_res = client.post("/api/auth/verify-otp", json={
        "email_or_username": "hoangtrituong",
        "otp_code": otp_code,
        "new_password": "newpass123456"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "success"

    # 3. Login with new password
    login_res = client.post("/api/auth/login", json={
        "username": "hoangtrituong",
        "password": "newpass123456"
    })
    assert login_res.status_code == 200

    # 4. Reset back to the sample password
    client.post("/api/auth/forgot-password", json={
        "username_or_email": "hoangtrituong",
        "new_password": "Khachhang"
    })

def test_forgot_password_reports_smtp_failure(monkeypatch):
    monkeypatch.setattr(EmailService, "send_otp_reset_email", lambda **kwargs: {
        "success": False,
        "mode": "SMTP_ERROR",
        "message": "SMTP test failure"
    })

    response = client.post("/api/auth/send-otp", json={
        "email_or_username": "hoangtrituong"
    })

    assert response.status_code == 503
    assert response.json()["detail"] == "SMTP test failure"

def test_forgot_password_rejects_unregistered_email():
    response = client.post("/api/auth/send-otp", json={
        "email_or_username": "nonexistent_email_999999@test.com"
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "Không tìm thấy tài khoản với Email hoặc Tên đăng nhập này"

def test_forgot_password_direct():
    res = client.post("/api/auth/forgot-password", json={
        "username_or_email": "hoangtrituong",
        "new_password": "Khachhang"
    })
    assert res.status_code == 200
    assert "thành công" in res.json()["message"]
