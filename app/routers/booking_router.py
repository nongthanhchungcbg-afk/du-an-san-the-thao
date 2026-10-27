from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import (
    Booking, Pitch, BookingStatus, PitchStatus, User, UserRole, Customer, 
    Payment, PaymentType, PaymentMethod, PaymentStatus, UserActivityLog,
    WalletTransaction, WalletTransactionType, TimeSlot
)
from app.schemas import BookingCreate, BookingUpdate, BookingResponse, TimeSlotCreate
from app.auth import get_current_user, require_roles, get_current_active_user
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/bookings", tags=["Đặt Sân & Chống Trùng Lịch"])
timeslots_router = APIRouter(prefix="/api/timeslots", tags=["Khung Giờ Sân (Table 16)"])

def check_time_conflict(db: Session, pitch_id: int, booking_date: str, start_time: str, end_time: str, exclude_booking_id: Optional[int] = None) -> bool:
    query = db.query(Booking).filter(
        Booking.pitch_id == pitch_id,
        Booking.booking_date == booking_date,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        Booking.start_time < end_time,
        Booking.end_time > start_time
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    
    return query.first() is not None

def calculate_pitch_price(pitch: Pitch, start_time: str, end_time: str) -> float:
    try:
        sh, sm = map(int, start_time.split(":"))
        eh, em = map(int, end_time.split(":"))
        duration_hours = (eh * 60 + em - (sh * 60 + sm)) / 60.0
        if duration_hours <= 0:
            duration_hours = 1.0
        
        # Nếu rơi vào khung giờ cao điểm (>= 17h00)
        if sh >= 17:
            rate = pitch.peak_price_per_hour
        else:
            rate = pitch.price_per_hour
        return duration_hours * rate
    except Exception:
        return pitch.price_per_hour

@router.get("", response_model=List[BookingResponse])
def get_bookings(
    pitch_id: Optional[int] = None,
    booking_date: Optional[str] = None,
    status: Optional[BookingStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Booking)
    if pitch_id:
        query = query.filter(Booking.pitch_id == pitch_id)
    if booking_date:
        query = query.filter(Booking.booking_date == booking_date)
    if status:
        query = query.filter(Booking.status == status)
    return query.order_by(Booking.booking_date.desc(), Booking.start_time.asc()).all()

@router.get("/available-slots")
def get_available_slots(
    booking_date: Optional[str] = None,
    sport_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    target_date = booking_date or datetime.now().strftime("%Y-%m-%d")
    pitches_query = db.query(Pitch).filter(Pitch.status == PitchStatus.AVAILABLE)
    if sport_type:
        pitches_query = pitches_query.filter(Pitch.sport_type == sport_type)
    pitches = pitches_query.all()

    default_slots = [
        ("05:00", "06:00"), ("06:00", "07:00"), ("07:00", "08:00"), ("08:00", "09:00"),
        ("13:30", "14:30"), ("14:30", "16:00"), ("16:00", "17:30"),
        ("17:30", "19:00"), ("19:00", "20:30"), ("20:30", "22:00")
    ]

    available_list = []
    for pitch in pitches:
        bookings = db.query(Booking).filter(
            Booking.pitch_id == pitch.id,
            Booking.booking_date == target_date,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).all()

        for st, et in default_slots:
            is_booked = any(b.start_time < et and b.end_time > st for b in bookings)
            if not is_booked:
                available_list.append({
                    "pitch_id": pitch.id,
                    "pitch_name": pitch.name,
                    "sport_type": pitch.sport_type.value,
                    "location": pitch.location,
                    "start_time": st,
                    "end_time": et,
                    "booking_date": target_date,
                    "price_per_hour": pitch.price_per_hour,
                    "peak_price_per_hour": pitch.peak_price_per_hour
                })

    return {"date": target_date, "available_slots": available_list}

@router.get("/matrix")
def get_booking_matrix(
    start_date: Optional[str] = None,
    pitch_id: Optional[int] = None,
    time_frame: Optional[str] = "ALL", # MORNING, AFTERNOON, EVENING, ALL
    db: Session = Depends(get_db)
):
    if not start_date:
        start_dt = datetime.now()
    else:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except Exception:
            start_dt = datetime.now()

    dates = []
    vietnamese_days = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    for i in range(7):
        curr = start_dt + timedelta(days=i)
        dates.append({
            "date": curr.strftime("%Y-%m-%d"),
            "display": f"{vietnamese_days[curr.weekday()]} {curr.day}/{curr.month}",
            "day_name": vietnamese_days[curr.weekday()]
        })

    all_time_slots = [
        {"start": "05:00", "end": "06:00", "frame": "MORNING"},
        {"start": "06:00", "end": "07:00", "frame": "MORNING"},
        {"start": "07:00", "end": "08:00", "frame": "MORNING"},
        {"start": "08:00", "end": "09:00", "frame": "MORNING"},
        {"start": "09:00", "end": "10:00", "frame": "MORNING"},
        {"start": "10:00", "end": "11:30", "frame": "MORNING"},
        {"start": "13:30", "end": "14:30", "frame": "AFTERNOON"},
        {"start": "14:30", "end": "16:00", "frame": "AFTERNOON"},
        {"start": "16:00", "end": "17:30", "frame": "AFTERNOON"},
        {"start": "17:30", "end": "19:00", "frame": "EVENING"},
        {"start": "19:00", "end": "20:30", "frame": "EVENING"},
        {"start": "20:30", "end": "22:00", "frame": "EVENING"}
    ]

    if time_frame and time_frame != "ALL":
        time_slots = [s for s in all_time_slots if s["frame"] == time_frame]
    else:
        time_slots = all_time_slots

    selected_pitch = None
    if pitch_id:
        selected_pitch = db.query(Pitch).filter(Pitch.id == pitch_id).first()
    if not selected_pitch:
        selected_pitch = db.query(Pitch).filter(Pitch.status == PitchStatus.AVAILABLE).first()

    pitch_price = selected_pitch.price_per_hour if selected_pitch else 80000
    peak_price = selected_pitch.peak_price_per_hour if selected_pitch else 120000

    date_strs = [d["date"] for d in dates]
    bookings_query = db.query(Booking).filter(
        Booking.pitch_id == (selected_pitch.id if selected_pitch else 1),
        Booking.booking_date.in_(date_strs),
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).all()

    matrix_rows = []
    now_dt = datetime.now()

    for d in dates:
        row_slots = []
        for s in time_slots:
            slot_start_dt = datetime.strptime(f"{d['date']} {s['start']}", "%Y-%m-%d %H:%M")
            is_past = slot_start_dt < now_dt - timedelta(minutes=15)

            matched_b = next((b for b in bookings_query if b.booking_date == d["date"] and (b.start_time < s["end"] and b.end_time > s["start"])), None)

            if is_past:
                status_code = "EXPIRED"
                status_text = "Quá hạn"
                price = 0
            elif matched_b:
                if matched_b.status == BookingStatus.CONFIRMED or matched_b.status == BookingStatus.COMPLETED:
                    status_code = "BOOKED"
                    status_text = "Đã đặt"
                else:
                    status_code = "PENDING"
                    status_text = "Chờ duyệt"
                price = matched_b.total_price
            else:
                status_code = "AVAILABLE"
                sh = int(s["start"].split(":")[0])
                current_rate = peak_price if sh >= 17 else pitch_price
                price = current_rate
                status_text = f"{int(price):,}đ"

            row_slots.append({
                "start": s["start"],
                "end": s["end"],
                "slot_label": f"{s['start']} - {s['end']}",
                "status": status_code,
                "text": status_text,
                "price": price,
                "pitch_id": selected_pitch.id if selected_pitch else 1,
                "pitch_name": selected_pitch.name if selected_pitch else "",
                "date": d["date"]
            })

        matrix_rows.append({
            "date": d["date"],
            "display": d["display"],
            "day_name": d["day_name"],
            "slots": row_slots
        })

    return {
        "selected_pitch": selected_pitch,
        "time_slots": time_slots,
        "matrix": matrix_rows
    }

@router.post("", response_model=BookingResponse)
def create_booking(
    booking_in: BookingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    pitch = db.query(Pitch).filter(Pitch.id == booking_in.pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Sân thể thao không tồn tại")
    
    if pitch.status == PitchStatus.MAINTENANCE:
        raise HTTPException(status_code=400, detail="Sân đang trong thời gian bảo trì, quý khách vui lòng chọn sân khác")

    if check_time_conflict(db, booking_in.pitch_id, booking_in.booking_date, booking_in.start_time, booking_in.end_time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Trùng lịch: Sân '{pitch.name}' đã có người đặt trong khung giờ {booking_in.start_time} - {booking_in.end_time} ngày {booking_in.booking_date}. Vui lòng chọn khung giờ khác!"
        )

    configured_slots = db.query(TimeSlot).filter(
        TimeSlot.court_id == booking_in.pitch_id,
        TimeSlot.date == booking_in.booking_date
    ).all()
    if configured_slots and not any(
        slot.is_available
        and slot.start_time <= booking_in.start_time
        and slot.end_time >= booking_in.end_time
        for slot in configured_slots
    ):
        raise HTTPException(status_code=400, detail="Khung giờ này không nằm trong lịch sân đang mở bán")


    total_price = calculate_pitch_price(pitch, booking_in.start_time, booking_in.end_time)
    user_id = current_user.id if current_user else None
    invoice_email = (booking_in.invoice_email.strip() if booking_in.invoice_email else None) or (current_user.email if current_user else None) or f"{booking_in.customer_phone}@guest.vn"

    # Tự động đồng bộ / tạo khách hàng vào bảng Customer
    customer = db.query(Customer).filter(Customer.phone == booking_in.customer_phone.strip()).first()
    if not customer:
        customer = Customer(
            name=booking_in.customer_name.strip(),
            phone=booking_in.customer_phone.strip(),
            email=invoice_email
        )
        db.add(customer)
        db.flush()
    else:
        if booking_in.invoice_email and "@" in booking_in.invoice_email:
            customer.email = booking_in.invoice_email.strip()
            db.flush()
    customer_id = customer.id

    # Xử lý thanh toán qua Ví điện tử
    if booking_in.payment_method == PaymentMethod.WALLET:
        if not current_user:
            raise HTTPException(status_code=401, detail="Vui lòng đăng nhập để thanh toán bằng Ví điện tử")
        if (current_user.wallet_balance or 0.0) < total_price:
            raise HTTPException(
                status_code=400, 
                detail=f"Số dư ví không đủ (Hiện có: {current_user.wallet_balance or 0:,.0f} đ, cần: {total_price:,.0f} đ). Vui lòng nạp thêm tiền vào ví!"
            )
        current_user.wallet_balance -= total_price
        db.commit()

    is_paid_upfront = (booking_in.payment_method == PaymentMethod.WALLET) or (booking_in.deposit_amount and booking_in.deposit_amount >= total_price)

    new_booking = Booking(
        user_id=user_id,
        customer_id=customer_id,
        pitch_id=booking_in.pitch_id,
        customer_name=booking_in.customer_name,
        customer_phone=booking_in.customer_phone,
        booking_date=booking_in.booking_date,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        total_price=total_price,
        deposit_amount=total_price if booking_in.payment_method == PaymentMethod.WALLET else (booking_in.deposit_amount or (total_price if booking_in.payment_method == PaymentMethod.BANK_TRANSFER else 0.0)),
        payment_method=booking_in.payment_method or PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID if is_paid_upfront else PaymentStatus.PENDING,
        bank_name=booking_in.bank_name,
        status=BookingStatus.CONFIRMED if (is_paid_upfront or booking_in.payment_method == PaymentMethod.CASH) else BookingStatus.PENDING,
        note=booking_in.note,
        invoice_email=invoice_email
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    if booking_in.payment_method == PaymentMethod.WALLET:
        tx = WalletTransaction(
            user_id=current_user.id,
            amount=-total_price,
            transaction_type=WalletTransactionType.PAYMENT,
            payment_method="WALLET",
            status=PaymentStatus.PAID,
            description=f"Thanh toán đặt sân #{new_booking.id} ({pitch.name})",
            transaction_code=f"PAY{new_booking.id}"
        )
        db.add(tx)
        db.commit()

    if new_booking.deposit_amount > 0 or new_booking.payment_method in [PaymentMethod.BANK_TRANSFER, PaymentMethod.WALLET]:
        pay = Payment(
            booking_id=new_booking.id,
            amount=new_booking.deposit_amount if new_booking.deposit_amount > 0 else new_booking.total_price,
            payment_type=PaymentType.FULL_PAYMENT if is_paid_upfront else PaymentType.DEPOSIT,
            payment_method=new_booking.payment_method,
            status=new_booking.payment_status,
            bank_name=new_booking.bank_name,
            transaction_ref=f"TXN{new_booking.id}{int(datetime.utcnow().timestamp())}",
            note=f"Thanh toán cho đơn đặt #{new_booking.id}"
        )
        db.add(pay)
        db.commit()

    # Gửi email thật xác nhận đặt sân
    dest_email = (booking_in.invoice_email.strip() if booking_in.invoice_email else None) or (current_user.email if current_user else None) or (customer.email if customer and customer.email else None)
    email_send_result = None
    if dest_email and "@" in dest_email and not dest_email.endswith("@guest.vn"):
        email_send_result = EmailService.send_booking_confirmation_email(
            booking_dict={
                "id": new_booking.id,
                "customer_name": new_booking.customer_name,
                "booking_date": new_booking.booking_date,
                "start_time": new_booking.start_time,
                "end_time": new_booking.end_time,
                "total_price": new_booking.total_price,
                "deposit_amount": new_booking.deposit_amount,
                "payment_method": new_booking.payment_method.value
            },
            pitch_dict={
                "name": pitch.name,
                "sport_type": pitch.sport_type.value,
                "location": pitch.location
            },
            to_email=dest_email
        )

    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=user_id,
        customer_id=customer_id,
        username=current_user.username if current_user else booking_in.customer_name,
        action=f"Tạo đơn đặt sân #{new_booking.id} ({pitch.name} lúc {new_booking.start_time}-{new_booking.end_time} {new_booking.booking_date})",
        role=current_user.role.value if current_user else "GUEST",
        ip_address=client_ip
    )
    db.add(log)
    db.commit()

    new_booking.email_result = email_send_result
    return new_booking

@router.get("/my-bookings", response_model=List[BookingResponse])
def get_my_bookings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Booking).filter(
        or_(Booking.user_id == current_user.id, Booking.customer_phone == current_user.phone)
    ).order_by(Booking.booking_date.desc(), Booking.start_time.desc()).all()

@router.post("/{booking_id}/confirm-and-send-invoice")
def confirm_and_send_invoice(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")

    booking.status = BookingStatus.CONFIRMED
    booking.payment_status = PaymentStatus.PAID
    booking.invoice_sent = True

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if payment:
        payment.status = PaymentStatus.PAID
    else:
        payment = Payment(
            booking_id=booking.id,
            amount=booking.total_price,
            payment_type=PaymentType.FULL_PAYMENT,
            payment_method=booking.payment_method,
            status=PaymentStatus.PAID,
            note="Xác nhận thanh toán hoàn tất bởi Ban Quản Trị"
        )
        db.add(payment)

    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=current_user.id,
        username=current_user.username,
        action=f"Xác nhận thanh toán và gửi hóa đơn điện tử cho đơn #{booking.id} ({booking.customer_name})",
        role=current_user.role.value,
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    db.refresh(booking)

    # Gửi email hóa đơn điện tử & thông báo duyệt đơn
    dest_email = booking.invoice_email or (booking.user.email if booking.user else None) or (booking.customer.email if booking.customer else None) or "nongthanhchungcbg@gmail.com"
    email_res = None
    if dest_email:
        email_res = EmailService.send_invoice_email(
            booking_dict={
                "id": booking.id,
                "customer_name": booking.customer_name,
                "pitch_name": booking.pitch.name if booking.pitch else "Sân Thể Thao",
                "total_price": booking.total_price,
                "booking_date": booking.booking_date,
                "start_time": booking.start_time,
                "end_time": booking.end_time
            },
            to_email=dest_email
        )

    msg = f"Đã duyệt đơn #{booking.id} thành công!"
    if email_res and email_res.get("mode") == "LIVE_SMTP":
        msg += f" Đã gửi hóa đơn điện tử trực tiếp đến {dest_email} qua SMTP."
    elif dest_email:
        msg += f" (Chú ý: Chưa cấu hình SMTP_USER trong .env, thư đã được lưu tự động vào Hộp Thư Hệ Thống Local Outbox)."

    return {
        "status": "success",
        "message": msg,
        "booking_id": booking.id,
        "invoice_number": f"HD-STT-{booking.id:05d}",
        "sent_to": dest_email,
        "email_result": email_res
    }

@router.get("/outbox-emails")
def get_system_outbox_emails():
    return EmailService.get_outbox_emails()


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking_detail(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
    return booking

@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    booking_in: BookingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")

    new_pitch_id = booking_in.pitch_id if booking_in.pitch_id is not None else booking.pitch_id
    new_date = booking_in.booking_date if booking_in.booking_date is not None else booking.booking_date
    new_start = booking_in.start_time if booking_in.start_time is not None else booking.start_time
    new_end = booking_in.end_time if booking_in.end_time is not None else booking.end_time

    time_or_pitch_changed = (
        new_pitch_id != booking.pitch_id or 
        new_date != booking.booking_date or 
        new_start != booking.start_time or 
        new_end != booking.end_time
    )

    pitch = db.query(Pitch).filter(Pitch.id == new_pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Không tìm thấy sân thể thao này")

    if time_or_pitch_changed:
        try:
            sh, sm = map(int, new_start.split(":"))
            eh, em = map(int, new_end.split(":"))
            start_minutes = sh * 60 + sm
            end_minutes = eh * 60 + em
            if end_minutes <= start_minutes:
                raise HTTPException(status_code=400, detail="Giờ kết thúc phải sau giờ bắt đầu")
        except ValueError:
            raise HTTPException(status_code=400, detail="Định dạng giờ không hợp lệ (HH:MM)")

        conflicts = db.query(Booking).filter(
            Booking.pitch_id == new_pitch_id,
            Booking.booking_date == new_date,
            Booking.id != booking_id,
            Booking.status != BookingStatus.CANCELLED,
            Booking.start_time < new_end,
            Booking.end_time > new_start
        ).all()

        if conflicts:
            conf_details = [f"#{c.id} ({c.start_time}-{c.end_time})" for c in conflicts]
            raise HTTPException(
                status_code=409,
                detail=f"Trùng lịch! Khung giờ {new_start}-{new_end} ngày {new_date} trên {pitch.name} đã có người đặt: {', '.join(conf_details)}"
            )

        duration_hours = (end_minutes - start_minutes) / 60.0
        if sh >= 17:
            rate = pitch.peak_price_per_hour or pitch.price_per_hour
        else:
            rate = pitch.price_per_hour
        total_price = round(duration_hours * rate)
        booking.total_price = total_price

    if booking_in.pitch_id is not None:
        booking.pitch_id = booking_in.pitch_id
    if booking_in.booking_date is not None:
        booking.booking_date = booking_in.booking_date
    if booking_in.start_time is not None:
        booking.start_time = booking_in.start_time
    if booking_in.end_time is not None:
        booking.end_time = booking_in.end_time
    if booking_in.customer_name is not None:
        booking.customer_name = booking_in.customer_name
    if booking_in.customer_phone is not None:
        booking.customer_phone = booking_in.customer_phone
    if booking_in.deposit_amount is not None:
        booking.deposit_amount = booking_in.deposit_amount
    if booking_in.status is not None:
        booking.status = booking_in.status
    if booking_in.payment_status is not None:
        booking.payment_status = booking_in.payment_status
    if booking_in.note is not None:
        booking.note = booking_in.note
    if booking_in.invoice_email is not None:
        booking.invoice_email = booking_in.invoice_email

    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=current_user.id if current_user else None,
        username=current_user.username if current_user else booking.customer_name,
        action=f"Cập nhật / Đổi lịch đơn đặt sân #{booking.id} ({pitch.name} ngày {booking.booking_date} lúc {booking.start_time}-{booking.end_time})",
        role=current_user.role.value if current_user else "GUEST",
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    db.refresh(booking)

    dest_email = booking.invoice_email or (booking.user.email if booking.user else None)
    if dest_email and "@" in dest_email:
        EmailService.send_booking_confirmation_email(
            booking_dict={
                "id": booking.id,
                "customer_name": booking.customer_name,
                "booking_date": booking.booking_date,
                "start_time": booking.start_time,
                "end_time": booking.end_time,
                "total_price": booking.total_price,
                "deposit_amount": booking.deposit_amount,
                "payment_method": booking.payment_method.value if booking.payment_method else "CASH"
            },
            pitch_dict={
                "name": pitch.name,
                "sport_type": pitch.sport_type.value,
                "location": pitch.location
            },
            to_email=dest_email
        )

    return booking

@router.post("/{booking_id}/complete")
def complete_booking(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Chỉ có thể hoàn tất đơn đã được xác nhận")
    try:
        booking_end = datetime.strptime(f"{booking.booking_date} {booking.end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Ngày hoặc giờ của đơn đặt sân không hợp lệ")
    if booking_end > datetime.now():
        raise HTTPException(status_code=400, detail="Chỉ có thể hoàn tất đơn sau khi khung giờ thuê kết thúc")

    booking.status = BookingStatus.COMPLETED
    client_ip = request.client.host if request.client else "127.0.0.1"
    db.add(UserActivityLog(
        user_id=current_user.id,
        username=current_user.username,
        action=f"Xác nhận khách đã trả sân, hoàn tất đơn #{booking.id}",
        role=current_user.role.value,
        ip_address=client_ip
    ))
    db.commit()
    return {"status": "success", "message": f"Đã xác nhận trả sân và hoàn tất đơn #{booking.id}"}

@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")

    booking.status = BookingStatus.CANCELLED
    booking.payment_status = PaymentStatus.REFUNDED
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=current_user.id if current_user else None,
        username=current_user.username if current_user else "Khách",
        action=f"Hủy đơn đặt sân #{booking.id}",
        role=current_user.role.value if current_user else "GUEST",
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    return {"message": f"Đã hủy đơn đặt sân #{booking_id} thành công"}



@router.get("/timeslots")
@timeslots_router.get("")
def get_timeslots_endpoint(
    court_id: Optional[int] = None,
    pitch_id: Optional[int] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    target_pitch_id = court_id or pitch_id
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    
    pitch = None
    if target_pitch_id:
        pitch = db.query(Pitch).filter(Pitch.id == target_pitch_id).first()
    if not pitch:
        pitch = db.query(Pitch).filter(Pitch.status == PitchStatus.AVAILABLE).first()

    default_slots = [
        ("05:00", "06:00"), ("06:00", "07:00"), ("07:00", "08:00"), ("08:00", "09:00"),
        ("09:00", "10:00"), ("10:00", "11:30"), ("13:30", "14:30"), ("14:30", "16:00"),
        ("16:00", "17:30"), ("17:30", "19:00"), ("19:00", "20:30"), ("20:30", "22:00")
    ]

    bookings = db.query(Booking).filter(
        Booking.pitch_id == (pitch.id if pitch else 1),
        Booking.booking_date == target_date,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).all()

    configured_slots = db.query(TimeSlot).filter(
        TimeSlot.court_id == (pitch.id if pitch else 1),
        TimeSlot.date == target_date
    ).all()
    configured_by_range = {(slot.start_time, slot.end_time): slot for slot in configured_slots}

    slot_items = []
    for st, et in default_slots:
        sh = int(st.split(":")[0])
        price = (pitch.peak_price_per_hour if sh >= 17 else pitch.price_per_hour) if pitch else 100000
        is_booked = any(b.start_time < et and b.end_time > st for b in bookings)
        configured = configured_by_range.pop((st, et), None)
        slot_items.append({
            "id": configured.id if configured else None,
            "start_time": st,
            "end_time": et,
            "price": price,
            "is_booked": is_booked,
            "is_available": configured.is_available if configured else True,
            "is_locked": configured is not None and not configured.is_available
        })

    for configured in configured_by_range.values():
        sh = int(configured.start_time.split(":")[0])
        price = (pitch.peak_price_per_hour if sh >= 17 else pitch.price_per_hour) if pitch else 100000
        is_booked = any(b.start_time < configured.end_time and b.end_time > configured.start_time for b in bookings)
        slot_items.append({
            "id": configured.id,
            "start_time": configured.start_time,
            "end_time": configured.end_time,
            "price": price,
            "is_booked": is_booked,
            "is_available": configured.is_available,
            "is_locked": not configured.is_available
        })
    slot_items.sort(key=lambda slot: slot["start_time"])

    return {
        "court_id": pitch.id if pitch else 1,
        "court_name": pitch.name if pitch else "Sân Thể Thao",
        "date": target_date,
        "slots": slot_items
    }

@router.post("/timeslots")
@timeslots_router.post("")
def create_timeslot_endpoint(
    slot_in: TimeSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    """Tạo khung giờ mới cho một sân (Chuẩn Bảng 2.11 - Admin)"""
    pitch = db.query(Pitch).filter(Pitch.id == slot_in.court_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Sân thể thao không tồn tại")
    try:
        start_minutes = sum(int(part) * factor for part, factor in zip(slot_in.start_time.split(":"), (60, 1)))
        end_minutes = sum(int(part) * factor for part, factor in zip(slot_in.end_time.split(":"), (60, 1)))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Giờ phải theo định dạng HH:MM")
    if end_minutes <= start_minutes:
        raise HTTPException(status_code=400, detail="Giờ kết thúc phải sau giờ bắt đầu")

    existing_slot = db.query(TimeSlot).filter(
        TimeSlot.court_id == slot_in.court_id,
        TimeSlot.date == slot_in.date,
        TimeSlot.start_time == slot_in.start_time,
        TimeSlot.end_time == slot_in.end_time
    ).first()
    if existing_slot:
        existing_slot.is_available = bool(slot_in.is_available)
        existing_slot.booking_id = slot_in.booking_id
        new_slot = existing_slot
    else:
        new_slot = TimeSlot(
            court_id=slot_in.court_id,
            date=slot_in.date,
            start_time=slot_in.start_time,
            end_time=slot_in.end_time,
            is_available=slot_in.is_available,
            booking_id=slot_in.booking_id
        )
        db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return {
        "status": "success",
        "message": "Tạo khung giờ thành công",
        "timeslot": {
            "id": new_slot.id,
            "court_id": new_slot.court_id,
            "date": new_slot.date,
            "start_time": new_slot.start_time,
            "end_time": new_slot.end_time,
            "is_available": new_slot.is_available
        }
    }

@router.delete("/timeslots/{slot_id}")
@timeslots_router.delete("/{slot_id}")
def delete_timeslot_endpoint(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    slot = db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Không tìm thấy khung giờ")
    db.delete(slot)
    db.commit()
    return {"status": "success", "message": "Đã xóa cấu hình khung giờ", "id": slot_id}

@router.get("/{booking_id}/check-conflict")
def check_booking_conflict_endpoint(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Đơn đặt sân không tồn tại")
    
    has_conflict = check_time_conflict(
        db, booking.pitch_id, booking.booking_date, 
        booking.start_time, booking.end_time, 
        exclude_booking_id=booking.id
    )
    return {
        "booking_id": booking.id,
        "has_conflict": has_conflict,
        "message": "Phát hiện xung đột lịch đặt sân!" if has_conflict else "Lịch đặt hợp lệ, không có xung đột."
    }

@router.delete("/{booking_id}")
def delete_or_cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Đơn đặt sân không tồn tại")
    
    booking.status = BookingStatus.CANCELLED
    db.commit()
    return {"message": "Đã hủy đơn đặt sân và giải phóng khung giờ thành công", "booking_id": booking_id, "status": "CANCELLED"}
