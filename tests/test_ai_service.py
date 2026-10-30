import uuid
import smtplib
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.routers import auth_router
from app.services.ai_service import AIService
from app.services.email_service import EmailService

client = TestClient(app)

def get_admin_headers():
    login_res = client.post("/api/auth/login", json={
        "username": "nongthanhchung",
        "password": "Admin"
    })
    assert login_res.status_code == 200
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}

def test_slot_suggestions_preserve_iso_date_and_preferred_time():
    selected_date = "2026-10-02"
    query = f"Tìm khung giờ sân BASKETBALL ngày {selected_date} ưu tiên giờ 17:00"
    slots = [
        {"booking_date": selected_date, "start_time": "05:00", "end_time": "06:00", "pitch_name": "Sân 1"},
        {"booking_date": selected_date, "start_time": "16:00", "end_time": "17:30", "pitch_name": "Sân 1"},
        {"booking_date": selected_date, "start_time": "17:30", "end_time": "19:00", "pitch_name": "Sân 1"},
        {"booking_date": selected_date, "start_time": "19:00", "end_time": "20:30", "pitch_name": "Sân 1"},
    ]

    parsed = AIService.parse_time_and_date(query, selected_date)
    result = AIService.generate_slot_suggestion(query, slots, selected_date, "17:00")

    assert parsed["date"] == selected_date
    assert [slot["start_time"] for slot in result["suggested_slots"]] == ["17:30", "16:00", "19:00"]

def test_ai_suggest_slots():
    res = client.post("/api/ai/suggest-slots", json={
        "user_query": "5h đến 6h ngày mai có sân nào trống không"
    })
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["response"]) > 10
    assert "source" in data
    assert len(data["suggested_slots"]) > 0

def test_ai_open_ended_questions():
    # 1. Hỏi về tập gym & tăng cơ
    res_gym = client.post("/api/ai/suggest-slots", json={
        "user_query": "Tư vấn cho tôi lịch tập gym và cách ăn để tăng cơ giảm mỡ hiệu quả"
    })
    assert res_gym.status_code == 200
    assert "Protein" in res_gym.json()["response"] or "cơ bắp" in res_gym.json()["response"]

    # 2. Hỏi về kỹ thuật cầu lông
    res_badminton = client.post("/api/ai/suggest-slots", json={
        "user_query": "Làm thế nào để đập cầu smash uy lực trong cầu lông?"
    })
    assert res_badminton.status_code == 200
    assert "Smash" in res_badminton.json()["response"] or "cầu lông" in res_badminton.json()["response"]

    # 3. Hỏi về dự án nhóm 3 ICTU
    res_project = client.post("/api/ai/suggest-slots", json={
        "user_query": "Dự án nhóm 3 học phần AIA331 gồm những thành viên nào?"
    })
    assert res_project.status_code == 200
    assert "Nông Thành Chung" in res_project.json()["response"] or "Nhóm 03" in res_project.json()["response"]

def test_ai_generate_notifications():
    # 1. Create a pitch if none exists
    p_res = client.get("/api/pitches")
    pitches = p_res.json()
    if not pitches:
        p_res = client.post("/api/pitches", json={
            "name": "Sân Test Bóng Đá",
            "sport_type": "FOOTBALL",
            "price_per_hour": 200000,
            "peak_price_per_hour": 300000,
            "location": "Cơ sở 1"
        })
        pitch_id = p_res.json()["id"]
    else:
        pitch_id = pitches[0]["id"]

    # 2. Create unique booking
    bk_res = client.post("/api/bookings", json={
        "pitch_id": pitch_id,
        "customer_name": "Nguyen AI Test",
        "customer_phone": "0988000111",
        "booking_date": "2029-08-15",
        "start_time": "05:00",
        "end_time": "06:00",
        "deposit_amount": 200000
    }, headers=get_admin_headers())
    if bk_res.status_code != 200:
        bk_list = client.get("/api/bookings").json()
        booking_id = bk_list[0]["id"]
    else:
        booking_id = bk_res.json()["id"]

    res = client.post("/api/ai/generate-notifications", json={
        "booking_id": booking_id,
        "notification_type": "CONFIRMATION"
    })
    assert res.status_code == 200
    data = res.json()
    assert "sms_message" in data
    assert "zalo_message" in data
    assert "email_content" in data


def test_ai_send_real_email_endpoint(monkeypatch):
    bk_list = client.get("/api/bookings").json()
    if bk_list and len(bk_list) > 0:
        booking_id = bk_list[0]["id"]
    else:
        p_res = client.get("/api/pitches")
        pitches = p_res.json()
        pitch_id = pitches[0]["id"] if pitches else 1
        bk_res = client.post("/api/bookings", json={
            "pitch_id": pitch_id,
            "customer_name": "Test Email Customer",
            "customer_phone": "0816227206",
            "booking_date": "2030-01-01",
            "start_time": "05:00",
            "end_time": "06:00",
            "payment_method": "CASH",
            "deposit_amount": 0.0,
            "invoice_email": "thanhchung.ictu@gmail.com"
        }, headers=get_admin_headers())
        booking_id = bk_res.json()["id"]

    monkeypatch.setattr(EmailService, "send_email", staticmethod(lambda **kwargs: {
        "success": True,
        "mode": "LIVE_SMTP",
        "message": "Sent by test SMTP"
    }))
    email_res = client.post("/api/ai/send-email", json={
        "booking_id": booking_id,
        "recipient_email": "thanhchung.ictu@gmail.com",
        "subject": f"Xác nhận đặt sân #{booking_id}",
        "content": "Kính gửi quý khách, đơn đặt sân của bạn đã được xác nhận thành công!"
    })
    assert email_res.status_code == 200
    assert email_res.json()["success"] is True
    assert email_res.json()["mode"] == "LIVE_SMTP"

def test_email_saved_to_outbox_is_not_reported_as_sent(monkeypatch, tmp_path):
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.setattr("app.services.email_service.settings.SMTP_USER", "")
    monkeypatch.setattr("app.services.email_service.settings.SMTP_PASSWORD", "")
    monkeypatch.setattr(EmailService, "_save_local_outbox", staticmethod(lambda *args: str(tmp_path / "draft.eml")))

    result = EmailService.send_email("customer@example.com", "Test", "Message")

    assert result["success"] is False
    assert result["mode"] == "LOCAL_OUTBOX"
    assert "CHƯA được gửi" in result["message"]

def test_email_service_uses_starttls_and_authenticated_sender(monkeypatch):
    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            calls.append(("connect", host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            calls.append(("close",))

        def ehlo(self):
            calls.append(("ehlo",))

        def starttls(self, context):
            calls.append(("starttls", context is not None))

        def login(self, username, password):
            calls.append(("login", username, password))

        def send_message(self, message, from_addr, to_addrs):
            calls.append(("send", from_addr, to_addrs, message["From"]))
            return {}

    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "application-password")
    monkeypatch.delenv("SMTP_FROM", raising=False)
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", FakeSMTP)

    result = EmailService.send_email("customer@example.com", "Subject", "Body")

    assert result["success"] is True
    assert result["mode"] == "LIVE_SMTP"
    assert ("starttls", True) in calls
    assert ("login", "sender@example.com", "application-password") in calls
    send_call = next(call for call in calls if call[0] == "send")
    assert send_call[1:3] == ("sender@example.com", ["customer@example.com"])

def test_smtp_disconnected_error_suggests_alternate_port(monkeypatch, tmp_path):
    class DisconnectedSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def ehlo(self):
            raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")

    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "application-password")
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", DisconnectedSMTP)
    monkeypatch.setattr(EmailService, "_save_local_outbox", staticmethod(lambda *args: str(tmp_path / "draft.eml")))

    result = EmailService.send_email("customer@example.com", "Subject", "Body")

    assert result["mode"] == "SMTP_ERROR"
    assert result["success"] is False
    assert "bước EHLO" in result["message"]
    assert "cấu hình cổng" in result["message"]
    assert "CHƯA được gửi" in result["message"]

def test_smtp_auth_disconnect_explains_account_password_mismatch(monkeypatch, tmp_path):
    class AuthDisconnectedSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def ehlo(self):
            return 250, b"OK"

        def starttls(self, context):
            return 220, b"Ready"

        def login(self, username, password):
            raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")

    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "application-password")
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP_SSL", AuthDisconnectedSMTP)
    monkeypatch.setattr(EmailService, "_save_local_outbox", staticmethod(lambda *args: str(tmp_path / "draft.eml")))

    result = EmailService.send_email("customer@example.com", "Subject", "Body")

    assert result["mode"] == "SMTP_ERROR"
    assert result["success"] is False
    assert "xác thực tài khoản" in result["message"]
    assert "App Password" in result["message"]
    assert "CHƯA được gửi" in result["message"]

def test_smtp_settings_endpoint_does_not_crash_on_missing_settings_import(monkeypatch):
    env_path = (Path(__file__).resolve().parents[1] / ".env").resolve()
    original_write_text = Path.write_text

    def avoid_persisting_smtp_test_credentials(path, data, *args, **kwargs):
        if path.resolve() == env_path:
            return len(data)
        return original_write_text(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", avoid_persisting_smtp_test_credentials)
    monkeypatch.setattr(auth_router.EmailService, "send_email", staticmethod(lambda **kwargs: {
        "success": False,
        "mode": "SMTP_ERROR",
        "message": "Controlled SMTP failure"
    }))
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    monkeypatch.setenv("SMTP_FROM", "")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "")

    response = client.post(
        "/api/auth/settings/smtp",
        headers=get_admin_headers(),
        json={
            "smtp_user": "dummy@example.com",
            "smtp_password": "not-a-real-password",
            "test_recipient": "dummy@example.com"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "warning"
    assert response.json()["test_result"]["message"] == "Controlled SMTP failure"

def test_ai_send_email_endpoint_returns_unsent_status(monkeypatch):
    monkeypatch.setattr(EmailService, "send_email", staticmethod(lambda **kwargs: {
        "success": False,
        "mode": "LOCAL_OUTBOX",
        "message": "SMTP chưa được cấu hình; thư được lưu ở outbox."
    }))
    bookings = client.get("/api/bookings").json()
    assert bookings

    response = client.post("/api/ai/send-email", json={
        "booking_id": bookings[0]["id"],
        "recipient_email": "customer@example.com",
        "subject": "Test",
        "content": "Message"
    })

    assert response.status_code == 200
    assert response.json()["success"] is False
