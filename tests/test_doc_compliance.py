import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Pitch, Booking, Customer, User, UserRole

client = TestClient(app)

def test_homepage_uses_one_background_video_without_clip_switcher():
    res = client.get("/")

    assert res.status_code == 200
    assert res.text.count('<video id="bg-hero-video"') == 1
    assert res.text.count('<source src="/static/videos/nensanthethao.mp4"') == 1
    assert "Clip 1" not in res.text
    assert "Clip 2" not in res.text
    assert "Clip 3" not in res.text
    assert "Clip 4" not in res.text

def get_admin_headers():
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_customers_crud():
    # 1. Create Customer
    res_create = client.post("/api/customers", json={
        "name": "Nguyen Van Báo Cáo",
        "phone": "0912345678",
        "email": "baocao@gmail.com",
        "address": "Thái Nguyên"
    })
    assert res_create.status_code == 201
    cust_id = res_create.json()["id"]
    assert res_create.json()["name"] == "Nguyen Van Báo Cáo"

    # 2. Get Customer List with search
    res_list = client.post("/api/customers", json={
        "name": "Le Thi C",
        "phone": "0987654321",
        "email": "lethi@gmail.com"
    })
    res_search = client.get("/api/customers?search=Báo Cáo")
    assert res_search.status_code == 200
    assert any(c["id"] == cust_id for c in res_search.json())

    # 3. Update Customer
    res_update = client.put(f"/api/customers/{cust_id}", json={
        "name": "Nguyen Van Báo Cáo (Updated)",
        "address": "TP. Thái Nguyên"
    })
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Nguyen Van Báo Cáo (Updated)"

    # 4. Delete Customer
    res_del = client.delete(f"/api/customers/{cust_id}")
    assert res_del.status_code == 200

def test_reports_dashboard_and_revenue():
    # 1. Dashboard Report
    res_dash = client.get("/api/reports/dashboard")
    assert res_dash.status_code == 200
    data = res_dash.json()
    assert "summary" in data
    assert "total_revenue" in data["summary"]
    assert "today_occupancy_rate" in data["summary"]

    # 2. Revenue Report (Day, Week, Month)
    for period in ["day", "week", "month"]:
        res_rev = client.get(f"/api/reports/revenue?period={period}")
        assert res_rev.status_code == 200
        rev_data = res_rev.json()
        assert "total_revenue" in rev_data
        assert "revenue_by_sport" in rev_data
        assert "revenue_by_day" in rev_data
        assert "peak_hours" in rev_data
        assert "loyal_customers" in rev_data

    # 3. Occupancy Report
    res_occ = client.get("/api/reports/occupancy")
    assert res_occ.status_code == 200
    assert "pitches_occupancy" in res_occ.json()

def test_table16_court_and_timeslot_endpoints():
    # 1. GET /api/courts
    res_courts = client.get("/api/courts")
    assert res_courts.status_code == 200
    assert len(res_courts.json()) > 0

    # 2. GET /api/court-types & POST /api/court-types
    res_types = client.get("/api/court-types")
    assert res_types.status_code == 200
    assert len(res_types.json()) > 0

    # 3. GET /api/timeslots
    res_slots = client.get("/api/timeslots")
    assert res_slots.status_code == 200
    slots_data = res_slots.json()
    assert "slots" in slots_data
    assert len(slots_data["slots"]) > 0

def test_table16_booking_conflict_and_payments_by_booking():
    db = SessionLocal()
    pitch = db.query(Pitch).first()
    pitch_id = pitch.id
    db.close()

    # Create a booking
    res_book = client.post("/api/bookings", json={
        "pitch_id": pitch_id,
        "customer_name": "Test Conflict User",
        "customer_phone": "0999888777",
        "booking_date": "2026-12-30",
        "start_time": "14:30",
        "end_time": "16:00",
        "payment_method": "CASH"
    })
    assert res_book.status_code == 200
    b_id = res_book.json()["id"]

    # Check conflict endpoint
    res_conf = client.get(f"/api/bookings/{b_id}/check-conflict")
    assert res_conf.status_code == 200
    assert "has_conflict" in res_conf.json()

    # Get payments by booking
    res_pays = client.get(f"/api/payments/booking/{b_id}")
    assert res_pays.status_code == 200

    # Delete booking
    res_del = client.delete(f"/api/bookings/{b_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "CANCELLED"

def test_table16_ai_aliases():
    # 1. GET /api/ai/suggest-slot
    res_suggest = client.get("/api/ai/suggest-slot?court_type=bóng đá&preferred_time=17:30")
    assert res_suggest.status_code == 200
    assert "suggested_slots" in res_suggest.json()

    # 2. POST /api/ai/generate-message
    db = SessionLocal()
    b = db.query(Booking).first()
    b_id = b.id if b else 1
    db.close()

    res_msg = client.post("/api/ai/generate-message", json={"booking_id": b_id})
    assert res_msg.status_code == 200
    assert "sms_message" in res_msg.json() and "zalo_message" in res_msg.json()

    # 3. GET /api/ai/summary
    res_sum = client.get("/api/ai/summary?month=09/2026")
    assert res_sum.status_code == 200
    assert "summary" in res_sum.json()
