from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Payment, Booking, PaymentStatus, BookingStatus, UserRole
from app.schemas import PaymentCreate, PaymentResponse
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/payments", tags=["Thanh Toán & Hóa Đơn (Table 14 & 16)"])

@router.get("", response_model=List[PaymentResponse])
def get_payments(
    booking_id: Optional[int] = None,
    status: Optional[PaymentStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Payment)
    if booking_id:
        query = query.filter(Payment.booking_id == booking_id)
    if status:
        query = query.filter(Payment.status == status)
    return query.order_by(Payment.created_at.desc()).all()

@router.get("/booking/{booking_id}", response_model=List[PaymentResponse])
def get_payments_by_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Đơn đặt sân không tồn tại")
    return db.query(Payment).filter(Payment.booking_id == booking_id).order_by(Payment.created_at.desc()).all()

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == payment_in.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin đơn đặt sân để thanh toán")
    
    new_payment = Payment(
        booking_id=payment_in.booking_id,
        amount=payment_in.amount,
        payment_type=payment_in.payment_type,
        payment_method=payment_in.payment_method,
        status=PaymentStatus.PAID,
        transaction_ref=payment_in.transaction_ref or f"PAY{booking.id}{int(datetime.now().timestamp()) % 100000}",
        bank_name=payment_in.bank_name or booking.bank_name,
        note=payment_in.note
    )
    db.add(new_payment)

    booking.payment_status = PaymentStatus.PAID
    booking.status = BookingStatus.CONFIRMED
    db.commit()
    db.refresh(new_payment)
    return new_payment
