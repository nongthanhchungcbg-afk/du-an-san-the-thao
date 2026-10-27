from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMIN"

def test_login_wrong_password():
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "sai_password"
    })
    assert res.status_code == 401

def test_forgot_password_otp_flow():
    # 1. Send OTP 4 digits
    send_res = client.post("/api/auth/send-otp", json={
        "email_or_username": "khachhang"
    })
    assert send_res.status_code == 200
    data = send_res.json()
    assert "demo_otp_hint" in data
    otp_code = data["demo_otp_hint"]
    assert len(otp_code) == 4

    # 2. Verify OTP & Reset Password
    verify_res = client.post("/api/auth/verify-otp", json={
        "email_or_username": "khachhang",
        "otp_code": otp_code,
        "new_password": "newpass123456"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "success"

    # 3. Login with new password
    login_res = client.post("/api/auth/login", json={
        "username": "khachhang",
        "password": "newpass123456"
    })
    assert login_res.status_code == 200

    # 4. Reset back to user123
    client.post("/api/auth/forgot-password", json={
        "username_or_email": "khachhang",
        "new_password": "user123"
    })

def test_forgot_password_direct():
    res = client.post("/api/auth/forgot-password", json={
        "username_or_email": "khachhang",
        "new_password": "user123"
    })
    assert res.status_code == 200
    assert "thành công" in res.json()["message"]
