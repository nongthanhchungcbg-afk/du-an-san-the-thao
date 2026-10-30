import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Pitch, Booking, PitchType, PitchStatus

client = TestClient(app)

def get_admin_headers():
    login_res = client.post("/api/auth/login", json={
        "username": "nongthanhchung",
        "password": "Admin"
    })
    assert login_res.status_code == 200
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}

@pytest.fixture(autouse=True)
def cleanup_test_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Xoa cac booking test cu
    db.query(Booking).filter(Booking.booking_date.in_(["2026-12-25", "2026-12-26"])).delete()
    db.query(Booking).filter(Booking.customer_phone == "0988999000").delete()
    if db.query(Pitch).count() == 0:
        p = Pitch(
            name="Sân Test 1",
            sport_type=PitchType.FOOTBALL,
            price_per_hour=300000,
            peak_price_per_hour=400000,
            status=PitchStatus.AVAILABLE
        )
        db.add(p)
    db.commit()
    db.close()

def test_create_booking_requires_login():
    res = client.post("/api/bookings", json={
        "pitch_id": 1,
        "customer_name": "Guest User",
        "customer_phone": "0988000000",
        "booking_date": "2026-12-25",
        "start_time": "17:30",
        "end_time": "19:00"
    })
    assert res.status_code == 401

def test_create_booking_success():
    res = client.post("/api/bookings", json={
        "pitch_id": 1,
        "customer_name": "Test User A",
        "customer_phone": "0988111222",
        "booking_date": "2026-12-25",
        "start_time": "17:30",
        "end_time": "19:00",
        "deposit_amount": 100000,
        "note": "Test đơn hàng hợp lệ"
    }, headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["customer_name"] == "Test User A"
    assert data["total_price"] > 0

def test_create_overlapping_booking_fails():
    # 1. Tao don dat san dau tien
    headers = get_admin_headers()
    client.post("/api/bookings", json={
        "pitch_id": 1,
        "customer_name": "Test User A1",
        "customer_phone": "0988111222",
        "booking_date": "2026-12-26",
        "start_time": "17:30",
        "end_time": "19:00",
        "deposit_amount": 100000
    }, headers=headers)

    # 2. Thu dat trung gio tren cung san ngay 2026-12-26 tu 18:00 den 19:30
    res = client.post("/api/bookings", json={
        "pitch_id": 1,
        "customer_name": "Test User B (Trùng giờ)",
        "customer_phone": "0988333444",
        "booking_date": "2026-12-26",
        "start_time": "18:00",
        "end_time": "19:30",
        "deposit_amount": 0
    }, headers=headers)
    # Bat buoc phai tra ve 409 Conflict
    assert res.status_code == 409
    assert "Trùng lịch" in res.json()["detail"]

def test_admin_can_mark_confirmed_booking_completed_after_return():
    login_res = client.post("/api/auth/login", json={
        "username": "nongthanhchung",
        "password": "Admin"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    pitches = client.get("/api/pitches").json()
    assert pitches

    booking_res = client.post("/api/bookings", json={
        "pitch_id": pitches[0]["id"],
        "customer_name": "Test Return Booking",
        "customer_phone": "0988999000",
        "booking_date": "2000-01-01",
        "start_time": "05:00",
        "end_time": "06:00",
        "payment_method": "CASH",
        "deposit_amount": 0
    }, headers={"Authorization": f"Bearer {token}"})
    assert booking_res.status_code == 200
    booking_id = booking_res.json()["id"]

    complete_res = client.post(
        f"/api/bookings/{booking_id}/complete",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert complete_res.status_code == 200
    assert client.get(f"/api/bookings/{booking_id}").json()["status"] == "COMPLETED"
