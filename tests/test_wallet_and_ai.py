import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, UserRole, Pitch, PitchType, PitchStatus, PaymentMethod, Booking, WalletTransaction, WalletTransactionType
from app.auth import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clean up test pitch bookings
    db.query(Booking).filter(Booking.pitch_id == 99).delete()

    # Create test users
    admin_user = db.query(User).filter(User.username == "testadmin").first()
    if not admin_user:
        admin_user = User(
            username="testadmin",
            email="testadmin@thehinhtre.vn",
            hashed_password=get_password_hash("admin123"),
            full_name="Quản Trị Viên Thành Chung Test",
            phone="0816227206",
            role=UserRole.ADMIN,
            wallet_balance=2000000.0
        )
        db.add(admin_user)

    cust_user = db.query(User).filter(User.username == "testcustomer").first()
    if not cust_user:
        cust_user = User(
            username="testcustomer",
            email="testcustomer@gmail.com",
            hashed_password=get_password_hash("cust123"),
            full_name="Khách Hàng Test",
            phone="0988776655",
            role=UserRole.CUSTOMER,
            wallet_balance=500000.0
        )
        db.add(cust_user)
    else:
        cust_user.wallet_balance = 500000.0

    # Create test pitch
    test_pitch = db.query(Pitch).filter(Pitch.id == 99).first()
    if not test_pitch:
        test_pitch = Pitch(
            id=99,
            name="Sân Test Đá Bóng 5 Người",
            sport_type=PitchType.FOOTBALL,
            location="Cơ sở 1: 128 Đường Z115",
            price_per_hour=200000,
            peak_price_per_hour=300000,
            status=PitchStatus.AVAILABLE,
            image_url="https://images.unsplash.com/photo-1529900245534-47fbf8204bca?w=700"
        )
        db.add(test_pitch)

    db.commit()
    yield
    db.close()


def test_ai_chat_general_and_system():
    # Test price query
    resp = client.post("/api/ai/chat", json={"message": "Bảng giá thuê sân bóng đá và cầu lông bao nhiêu?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "BẢNG GIÁ" in data["reply"] or "250.000" in data["reply"] or "Sân" in data["reply"]

    # Test Gym query (outside system sports knowledge)
    resp_gym = client.post("/api/ai/chat", json={"message": "Lịch tập Gym tăng cơ ngực và ăn bao nhiêu protein?"})
    assert resp_gym.status_code == 200
    data_gym = resp_gym.json()
    assert "reply" in data_gym
    assert "Gym" in data_gym["reply"] or "Protein" in data_gym["reply"] or "ngực" in data_gym["reply"]

    # Test contact / hotline
    resp_hotline = client.post("/api/ai/chat", json={"message": "Cho tôi số điện thoại hotline liên hệ quản lý"})
    assert resp_hotline.status_code == 200
    data_hotline = resp_hotline.json()
    assert "0816227206" in data_hotline["reply"]


def test_wallet_deposit_flow():
    token = create_access_token(data={"sub": "testcustomer", "role": "CUSTOMER"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Request deposit QR
    resp = client.post("/api/wallet/deposit-request", json={"amount": 200000, "bank_name": "MB"}, headers=headers)
    assert resp.status_code == 200
    qr_data = resp.json()
    assert qr_data["amount"] == 200000
    assert "0816227206" in qr_data["qr_url"]
    assert "NAPVI" in qr_data["transfer_content"]

    # 2. Confirm deposit
    resp_confirm = client.post("/api/wallet/confirm-deposit", json={"amount": 200000, "bank_name": "MB"}, headers=headers)
    assert resp_confirm.status_code == 200
    confirm_data = resp_confirm.json()
    assert confirm_data["wallet_balance"] >= 700000
    assert "user_id" in confirm_data

    # 3. Check wallet me
    resp_me = client.get("/api/wallet/me", headers=headers)
    assert resp_me.status_code == 200
    me_data = resp_me.json()
    assert me_data["wallet_balance"] >= 700000
    assert len(me_data["transactions"]) > 0


def test_booking_payment_via_wallet():
    token = create_access_token(data={"sub": "testcustomer", "role": "CUSTOMER"})
    headers = {"Authorization": f"Bearer {token}"}

    # Book pitch using WALLET
    booking_payload = {
        "customer_name": "Khách Hàng Test",
        "customer_phone": "0988776655",
        "pitch_id": 99,
        "booking_date": "2026-10-15",
        "start_time": "08:00",
        "end_time": "09:00",
        "payment_method": "WALLET",
        "note": "Thanh toán bằng ví điện tử"
    }
    resp = client.post("/api/bookings", json=booking_payload, headers=headers)
    assert resp.status_code == 200
    b_data = resp.json()
    assert b_data["payment_method"] == "WALLET"
    assert b_data["payment_status"] == "PAID"
    assert b_data["status"] == "CONFIRMED"

    # Verify customer my-bookings list
    resp_my = client.get("/api/bookings/my-bookings", headers=headers)
    assert resp_my.status_code == 200
    my_bookings = resp_my.json()
    assert any(b["id"] == b_data["id"] for b in my_bookings)


def test_booking_with_insufficient_wallet_balance_fails():
    # Register poor user with 0 balance
    db = SessionLocal()
    poor_user = db.query(User).filter(User.username == "poor_user").first()
    if not poor_user:
        poor_user = User(
            username="poor_user",
            email="poor@gmail.com",
            hashed_password=get_password_hash("pass123"),
            full_name="Poor User",
            phone="0911000000",
            role=UserRole.CUSTOMER,
            wallet_balance=1000.0
        )
        db.add(poor_user)
        db.commit()
    else:
        poor_user.wallet_balance = 1000.0
        db.commit()
    db.close()

    token = create_access_token(data={"sub": "poor_user", "role": "CUSTOMER"})
    headers = {"Authorization": f"Bearer {token}"}

    booking_payload = {
        "customer_name": "Poor User",
        "customer_phone": "0911000000",
        "pitch_id": 99,
        "booking_date": "2026-10-16",
        "start_time": "08:00",
        "end_time": "09:00",
        "payment_method": "WALLET"
    }
    resp = client.post("/api/bookings", json=booking_payload, headers=headers)
    assert resp.status_code == 400
    assert "Số dư ví không đủ" in resp.json()["detail"]
