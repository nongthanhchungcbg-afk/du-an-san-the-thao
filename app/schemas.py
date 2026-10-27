from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models import (
    UserRole, PitchType, PitchStatus, BookingStatus, 
    PaymentType, PaymentMethod, PaymentStatus, MaintenanceStatus, WalletTransactionType
)

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    hometown: Optional[str] = None
    birth_year: Optional[int] = None
    role: UserRole = UserRole.CUSTOMER

class UserCreate(UserBase):
    password: str

class UserRoleUpdate(BaseModel):
    role: UserRole

class UserResponse(UserBase):
    id: int
    wallet_balance: float = 0.0
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

class SendOTPRequest(BaseModel):
    email_or_username: str

class VerifyOTPRequest(BaseModel):
    email_or_username: str
    otp_code: str
    new_password: str

# Pitch Schemas
class PitchBase(BaseModel):
    name: str
    sport_type: PitchType
    location: Optional[str] = "Cơ sở 1: 128 Đường Z115, Tân Thịnh, TP. Thái Nguyên"
    capacity: Optional[str] = "5 - 7 người"
    price_per_hour: float
    peak_price_per_hour: float
    status: PitchStatus = PitchStatus.AVAILABLE
    description: Optional[str] = None
    image_url: Optional[str] = None

class PitchCreate(PitchBase):
    pass

class PitchUpdate(BaseModel):
    name: Optional[str] = None
    sport_type: Optional[PitchType] = None
    location: Optional[str] = None
    capacity: Optional[str] = None
    price_per_hour: Optional[float] = None
    peak_price_per_hour: Optional[float] = None
    status: Optional[PitchStatus] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class PitchResponse(PitchBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Booking Schemas
class BookingBase(BaseModel):
    pitch_id: int
    customer_name: str
    customer_phone: str
    booking_date: str  # YYYY-MM-DD
    start_time: str    # HH:MM
    end_time: str      # HH:MM
    deposit_amount: Optional[float] = 0.0
    payment_method: Optional[PaymentMethod] = PaymentMethod.CASH
    bank_name: Optional[str] = None
    note: Optional[str] = None

class BookingCreate(BookingBase):
    invoice_email: Optional[str] = None

class BookingUpdate(BaseModel):
    pitch_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    hometown: Optional[str] = None
    birth_year: Optional[int] = None
    booking_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[BookingStatus] = None
    deposit_amount: Optional[float] = None
    payment_status: Optional[PaymentStatus] = None
    note: Optional[str] = None
    invoice_email: Optional[str] = None

class BookingResponse(BookingBase):
    id: int
    user_id: Optional[int] = None
    total_price: float
    status: BookingStatus
    payment_status: PaymentStatus
    invoice_sent: bool
    invoice_email: Optional[str] = None
    created_at: datetime
    pitch: Optional[PitchResponse] = None
    email_result: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)

# Payment Schemas
class PaymentBase(BaseModel):
    booking_id: int
    amount: float
    payment_type: PaymentType = PaymentType.FULL_PAYMENT
    payment_method: PaymentMethod = PaymentMethod.CASH
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_ref: Optional[str] = None
    bank_name: Optional[str] = None
    note: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Maintenance Schemas
class MaintenanceBase(BaseModel):
    pitch_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    cost: Optional[float] = 0.0
    status: Optional[Any] = "SCHEDULED"

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    pitch_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    cost: Optional[float] = None
    status: Optional[Any] = None

class MaintenanceResponse(BaseModel):
    id: int
    pitch_id: int
    start_date: str
    end_date: str
    reason: str
    cost: Optional[float] = 0.0
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    created_at: datetime
    pitch: Optional[PitchResponse] = None
    model_config = ConfigDict(from_attributes=True)

# Review Schemas
class ReviewCreate(BaseModel):
    customer_name: str
    rating: int
    comment: str
    pitch_id: Optional[int] = None

class ReviewResponse(BaseModel):
    id: int
    customer_name: str
    rating: int
    comment: str
    pitch_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# MatchPost Schemas
class MatchPostCreate(BaseModel):
    author_name: str
    sport_type: PitchType = PitchType.FOOTBALL
    team_level: Optional[str] = "Phong trào / Giao lưu vui"
    match_time: str
    contact_phone: str
    content: str

class MatchPostUpdate(BaseModel):
    author_name: Optional[str] = None
    sport_type: Optional[PitchType] = None
    team_level: Optional[str] = None
    match_time: Optional[str] = None
    contact_phone: Optional[str] = None
    hometown: Optional[str] = None
    birth_year: Optional[int] = None
    content: Optional[str] = None

class MatchPostResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    author_name: str
    sport_type: PitchType
    team_level: str
    match_time: str
    contact_phone: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# EventAnnouncement Schemas
class EventAnnouncementCreate(BaseModel):
    title: str
    category: str = "GIẢI ĐẤU"
    description: str
    event_date: str
    banner_url: Optional[str] = None

class EventAnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[str] = None
    banner_url: Optional[str] = None

class EventAnnouncementResponse(BaseModel):
    id: int
    title: str
    category: str
    description: str
    event_date: str
    banner_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Activity Log Schema
class UserActivityLogResponse(BaseModel):
    id: int
    username: str
    action: str
    role: str
    ip_address: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# Wallet Schemas
class WalletDepositRequest(BaseModel):
    amount: float
    bank_name: Optional[str] = "MB"

class WalletDepositResponse(BaseModel):
    transaction_code: str
    amount: float
    qr_url: str
    bank_name: str
    account_number: str
    account_name: str
    transfer_content: str
    message: str

class WalletTransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: WalletTransactionType
    payment_method: str
    status: PaymentStatus
    description: Optional[str] = None
    transaction_code: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WalletBalanceResponse(BaseModel):
    user_id: int
    wallet_balance: float
    full_name: str
    transactions: List[WalletTransactionResponse] = []

# AI Request/Response Schemas
class AIChatRequest(BaseModel):
    message: str
    sport_type: Optional[str] = None
    date: Optional[str] = None

class AIChatResponse(BaseModel):
    reply: str
    suggested_slots: List[dict] = []
    source: str

class AISlotSuggestionRequest(BaseModel):
    user_query: str
    sport_type: Optional[str] = None
    date: Optional[str] = None
    preferred_time: Optional[str] = None

class AISlotSuggestionResponse(BaseModel):
    response: str
    suggested_slots: List[dict]
    source: str

class AINotificationRequest(BaseModel):
    booking_id: int
    notification_type: str = "CONFIRMATION"

class AINotificationResponse(BaseModel):
    booking_id: int
    sms_message: str
    zalo_message: str
    email_subject: str
    email_content: str
    source: str

class AIOccupancyReportRequest(BaseModel):
    days_back: Optional[int] = 7

class AIOccupancyReportResponse(BaseModel):
    summary: str
    peak_hours_analysis: str
    off_peak_recommendations: str
    suggested_promotions: List[dict]
    source: str



class AISendEmailRequest(BaseModel):
    booking_id: int
    recipient_email: str
    subject: str
    content: str


# =========================================================================
# SCHEMAS CHO CUSTOMER & COURT TYPE (BẢNG 9, 12, 16 TRONG BÁO CÁO)
# =========================================================================
class CustomerBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    hometown: Optional[str] = None
    birth_year: Optional[int] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CourtTypeBase(BaseModel):
    name: str
    sport_type: Optional[PitchType] = None
    description: Optional[str] = None

class CourtTypeCreate(CourtTypeBase):
    pass

class CourtTypeUpdate(BaseModel):
    name: Optional[str] = None
    sport_type: Optional[PitchType] = None
    description: Optional[str] = None

class CourtTypeResponse(CourtTypeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    message: str
    conflict_booking: Optional[dict] = None

class TimeSlotItem(BaseModel):
    start_time: str
    end_time: str
    price: float
    is_booked: bool = False
    is_locked: bool = False

class TimeSlotsResponse(BaseModel):
    court_id: int
    court_name: str
    date: str
    slots: List[TimeSlotItem]

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    hometown: Optional[str] = None
    birth_year: Optional[int] = None
    email: Optional[EmailStr] = None

class TimeSlotCreate(BaseModel):
    court_id: int
    date: str
    start_time: str
    end_time: str
    is_available: Optional[bool] = True
    booking_id: Optional[int] = None

class TimeSlotResponse(BaseModel):
    id: int
    court_id: int
    date: str
    start_time: str
    end_time: str
    is_available: bool
    booking_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
