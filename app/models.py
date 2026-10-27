import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"

class PitchType(str, enum.Enum):
    FOOTBALL = "FOOTBALL"      # Sân bóng đá mini 5/7 người
    BADMINTON = "BADMINTON"    # Sân cầu lông
    TENNIS = "TENNIS"          # Sân tennis
    GYM = "GYM"                # Phòng tập thể hình / Gym
    BASKETBALL = "BASKETBALL"  # Sân bóng rổ

class PitchStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class PaymentType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    FULL_PAYMENT = "FULL_PAYMENT"

class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    MOMO = "MOMO"
    WALLET = "WALLET"

class WalletTransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"

class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    hometown = Column(String(100), nullable=True)
    birth_year = Column(Integer, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    wallet_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    reset_otp = Column(String(10), nullable=True)
    reset_otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    match_posts = relationship("MatchPost", back_populates="user")
    activity_logs = relationship("UserActivityLog", back_populates="user")
    wallet_transactions = relationship("WalletTransaction", back_populates="user", cascade="all, delete-orphan")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="customer")

class CourtType(Base):
    __tablename__ = "court_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sport_type = Column(Enum(PitchType), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    court_type_id = Column(Integer, ForeignKey("court_types.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False, default=0)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimeSlot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    court_id = Column(Integer, ForeignKey("pitches.id"), nullable=False)
    date = Column(String(10), nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    is_available = Column(Boolean, default=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(WalletTransactionType), default=WalletTransactionType.DEPOSIT)
    payment_method = Column(String(50), default="VIETQR")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PAID)
    description = Column(String(255), nullable=True)
    transaction_code = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wallet_transactions")

class Pitch(Base):
    __tablename__ = "pitches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sport_type = Column(Enum(PitchType), nullable=False)
    location = Column(String(255), default="Cơ sở 1: 128 Đường Z115, Tân Thịnh, TP. Thái Nguyên")
    capacity = Column(String(50), default="5 - 7 người", nullable=True)
    price_per_hour = Column(Float, nullable=False)
    peak_price_per_hour = Column(Float, nullable=False)
    status = Column(Enum(PitchStatus), default=PitchStatus.AVAILABLE)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="pitch", cascade="all, delete-orphan")
    maintenances = relationship("Maintenance", back_populates="pitch", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    pitch_id = Column(Integer, ForeignKey("pitches.id"), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    booking_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    start_time = Column(String(5), nullable=False)    # HH:MM (e.g. 17:30)
    end_time = Column(String(5), nullable=False)      # HH:MM (e.g. 19:00)
    total_price = Column(Float, nullable=False)
    deposit_amount = Column(Float, default=0.0)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    bank_name = Column(String(100), nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    note = Column(Text, nullable=True)
    invoice_sent = Column(Boolean, default=False)
    invoice_email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    pitch = relationship("Pitch", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_type = Column(Enum(PaymentType), default=PaymentType.FULL_PAYMENT)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_ref = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="payments")

class Maintenance(Base):
    __tablename__ = "maintenances"

    id = Column(Integer, primary_key=True, index=True)
    pitch_id = Column(Integer, ForeignKey("pitches.id"), nullable=False)
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    reason = Column(String(255), nullable=False)
    cost = Column(Float, default=0.0)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED)
    created_at = Column(DateTime, default=datetime.utcnow)

    pitch = relationship("Pitch", back_populates="maintenances")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_name = Column(String(100), nullable=False)
    rating = Column(Integer, default=5, nullable=False) # 1 - 5 stars
    comment = Column(Text, nullable=False)
    pitch_id = Column(Integer, ForeignKey("pitches.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")

class MatchPost(Base):
    __tablename__ = "match_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    author_name = Column(String(100), nullable=False)
    sport_type = Column(Enum(PitchType), default=PitchType.FOOTBALL)
    team_level = Column(String(50), default="Phong trào / Giao lưu vui")
    match_time = Column(String(100), nullable=False) # e.g. "17h30 Tối thứ Sáu 20/08"
    contact_phone = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="match_posts")

class EventAnnouncement(Base):
    __tablename__ = "event_announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="GIẢI ĐẤU") # GIẢI ĐẤU, KHUYẾN MÃI, THÔNG BÁO
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    event_date = Column(String(100), nullable=True)
    banner_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_id = Column(Integer, nullable=True)
    username = Column(String(50), nullable=True)
    role = Column(String(20), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_logs")
