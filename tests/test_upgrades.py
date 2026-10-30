import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, UserRole, Pitch, PitchType, PitchStatus, Booking, BookingStatus, Maintenance, MaintenanceStatus
from app.auth import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Create test admin
    admin = db.query(User).filter(User.username == "test_admin").first()
    if not admin:
        admin = User(
            username="test_admin",
            email="test_admin@gmail.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        
    # Create test pitch
    pitch = db.query(Pitch).filter(Pitch.name == "Test Pitch 1").first()
    if not pitch:
        pitch = Pitch(
            name="Test Pitch 1",
            sport_type=PitchType.FOOTBALL,
            location="Cơ sở 1",
            capacity="10 người",
            price_per_hour=200000,
            peak_price_per_hour=300000,
            status=PitchStatus.AVAILABLE
        )
        db.add(pitch)
        
    db.commit()
    db.close()

def get_admin_headers():
    token = create_access_token({"sub": "test_admin", "role": "ADMIN"})
    return {"Authorization": f"Bearer {token}"}

def test_pitch_capacity_and_edit():
    headers = get_admin_headers()
    # Create pitch
    res = client.post("/api/pitches", json={
        "name": "Sân Test Edit Mới",
        "sport_type": "BADMINTON",
        "location": "Cơ sở 1",
        "capacity": "2 - 4 người",
        "price_per_hour": 80000,
        "peak_price_per_hour": 120000,
        "status": "AVAILABLE",
        "description": "Sân test mô tả",
        "image_url": "https://example.com/pitch.jpg"
    }, headers=headers)
    assert res.status_code == 200
    pitch_id = res.json()["id"]
    assert res.json()["capacity"] == "2 - 4 người"

    # Update pitch
    res_update = client.put(f"/api/pitches/{pitch_id}", json={
        "capacity": "4 - 6 người",
        "price_per_hour": 90000
    }, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["capacity"] == "4 - 6 người"
    assert res_update.json()["price_per_hour"] == 90000

def test_booking_edit_and_conflict():
    headers = get_admin_headers()
    db = SessionLocal()
    pitch = db.query(Pitch).first()
    pitch_id = pitch.id
    # Clean up any previous test bookings on test date
    test_date = "2026-11-20"
    db.query(Booking).filter(Booking.pitch_id == pitch_id, Booking.booking_date == test_date).delete()
    db.commit()
    db.close()

    # Create Booking 1 (08:00 - 10:00)
    res1 = client.post("/api/bookings", json={
        "pitch_id": pitch_id,
        "customer_name": "Nguyen Van A",
        "customer_phone": "0988111222",
        "booking_date": test_date,
        "start_time": "08:00",
        "end_time": "10:00",
        "payment_method": "CASH"
    }, headers=headers)
    assert res1.status_code == 200
    b1_id = res1.json()["id"]

    # Create Booking 2 (14:00 - 16:00)
    res2 = client.post("/api/bookings", json={
        "pitch_id": pitch_id,
        "customer_name": "Tran Van B",
        "customer_phone": "0988333444",
        "booking_date": test_date,
        "start_time": "14:00",
        "end_time": "16:00",
        "payment_method": "CASH"
    }, headers=headers)
    assert res2.status_code == 200
    b2_id = res2.json()["id"]

    # Edit Booking 2 to overlap with Booking 1 (09:00 - 11:00) -> Should Fail with 409
    res_conflict = client.put(f"/api/bookings/{b2_id}", json={
        "start_time": "09:00",
        "end_time": "11:00"
    }, headers=headers)
    assert res_conflict.status_code == 409

    # Edit Booking 2 to valid time (17:00 - 19:00) -> Should succeed and recalculate price
    res_edit = client.put(f"/api/bookings/{b2_id}", json={
        "start_time": "17:00",
        "end_time": "19:00",
        "note": "Khách đổi ý sang đá giờ tối"
    }, headers=headers)
    assert res_edit.status_code == 200
    assert res_edit.json()["start_time"] == "17:00"
    assert res_edit.json()["end_time"] == "19:00"
    assert res_edit.json()["note"] == "Khách đổi ý sang đá giờ tối"

def test_maintenance_management():
    headers = get_admin_headers()
    db = SessionLocal()
    pitch = db.query(Pitch).first()
    pitch_id = pitch.id
    db.close()

    # Schedule maintenance
    res = client.post("/api/maintenances", json={
        "pitch_id": pitch_id,
        "start_date": "2026-11-01",
        "end_date": "2026-11-03",
        "reason": "Bảo dưỡng thảm cỏ định kỳ",
        "cost": 1500000,
        "status": "SCHEDULED"
    }, headers=headers)
    assert res.status_code == 200
    maint_id = res.json()["id"]

    # Update maintenance
    res_update = client.put(f"/api/maintenances/{maint_id}", json={
        "cost": 1800000,
        "status": "IN_PROGRESS"
    }, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["cost"] == 1800000
    assert res_update.json()["status"] == "IN_PROGRESS"

    # Complete maintenance
    res_comp = client.post(f"/api/maintenances/{maint_id}/complete", headers=headers)
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "DONE"

def test_community_matches_and_events_crud():
    headers = get_admin_headers()

    # Create event
    res_event = client.post("/api/community/events", json={
        "title": "Giải đấu Test",
        "category": "GIẢI ĐẤU",
        "description": "Mô tả sự kiện",
        "event_date": "30/08/2026"
    }, headers=headers)
    assert res_event.status_code == 200
    event_id = res_event.json()["id"]

    # Edit event
    res_event_edit = client.put(f"/api/community/events/{event_id}", json={
        "title": "Giải đấu Test Đã Đổi Tên"
    }, headers=headers)
    assert res_event_edit.status_code == 200
    assert res_event_edit.json()["title"] == "Giải đấu Test Đã Đổi Tên"

    # Delete event
    res_event_del = client.delete(f"/api/community/events/{event_id}", headers=headers)
    assert res_event_del.status_code == 200
