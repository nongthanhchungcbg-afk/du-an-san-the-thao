import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_service import AIService

client = TestClient(app)

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
    })
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


def test_ai_send_real_email_endpoint():
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
        })
        booking_id = bk_res.json()["id"]

    email_res = client.post("/api/ai/send-email", json={
        "booking_id": booking_id,
        "recipient_email": "thanhchung.ictu@gmail.com",
        "subject": f"Xác nhận đặt sân #{booking_id}",
        "content": "Kính gửi quý khách, đơn đặt sân của bạn đã được xác nhận thành công!"
    })
    assert email_res.status_code == 200
    assert email_res.json()["success"] is True
