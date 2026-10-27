from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Booking, Payment, Pitch, Maintenance, BookingStatus, PitchStatus, PaymentStatus

router = APIRouter(prefix="/api/reports", tags=["Báo Cáo & Thống Kê Chuẩn (Table 16)"])

@router.get("/dashboard")
def get_reports_dashboard(db: Session = Depends(get_db)):
    total_pitches = db.query(Pitch).count()
    available_pitches = db.query(Pitch).filter(Pitch.status == PitchStatus.AVAILABLE).count()
    maintenance_pitches = db.query(Pitch).filter(Pitch.status == PitchStatus.MAINTENANCE).count()
    
    total_bookings = db.query(Booking).count()
    confirmed_bookings = db.query(Booking).filter(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])).count()
    pending_bookings = db.query(Booking).filter(Booking.status == BookingStatus.PENDING).count()
    cancelled_bookings = db.query(Booking).filter(Booking.status == BookingStatus.CANCELLED).count()

    total_rev = db.query(func.sum(Booking.total_price)).filter(
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).scalar() or 0.0

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    today_rev = db.query(func.sum(Booking.total_price)).filter(
        Booking.booking_date == today_str,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).scalar() or 0.0

    # Calculate overall occupancy rate
    total_potential_slots = (total_pitches or 1) * 12 # 12 slots per day
    booked_today = db.query(Booking).filter(
        Booking.booking_date == today_str,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).count()
    occupancy_rate = min(100.0, round((booked_today / total_potential_slots) * 100.0, 1))

    return {
        "status": "success",
        "summary": {
            "total_pitches": total_pitches,
            "available_pitches": available_pitches,
            "maintenance_pitches": maintenance_pitches,
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "pending_bookings": pending_bookings,
            "cancelled_bookings": cancelled_bookings,
            "total_revenue": total_rev,
            "today_revenue": today_rev,
            "today_occupancy_rate": f"{occupancy_rate}%",
            "occupancy_numeric": occupancy_rate
        }
    }

@router.get("/revenue")
def get_revenue_report(
    period: str = Query("month", description="Khoảng thời gian: day, week, month"),
    db: Session = Depends(get_db)
):
    today = datetime.utcnow().date()
    if period == "day":
        start_date = end_date = today
        period_label = f"Hôm nay ({today:%Y-%m-%d})"
    elif period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
        period_label = f"Tuần này ({start_date:%Y-%m-%d} đến {end_date:%Y-%m-%d})"
    else:
        start_date = today.replace(day=1)
        end_date = today
        period_label = f"Tháng {today.month}/{today.year}"

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    bookings_query = db.query(Booking).filter(
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
        Booking.booking_date >= start_date_str,
        Booking.booking_date <= end_date_str
    )
    bookings = bookings_query.all()

    total_amount = sum(b.total_price for b in bookings)
    total_count = len(bookings)
    booking_items = [
        {
            "id": b.id,
            "customer_name": b.customer_name,
            "pitch_name": b.pitch.name if b.pitch else "Sân",
            "booking_date": b.booking_date,
            "start_time": b.start_time,
            "end_time": b.end_time,
            "total_price": b.total_price,
            "status": b.status.value
        }
        for b in bookings
    ]

    # Group revenue and booking counts by date and sport.
    by_sport = {}
    by_day = {}
    by_hour = {}
    for b in bookings:
        st = b.pitch.sport_type.value if b.pitch else "OTHER"
        by_sport[st] = by_sport.get(st, 0.0) + b.total_price
        by_day[b.booking_date] = by_day.get(b.booking_date, 0.0) + b.total_price
        hour = b.start_time[:2]
        bucket = by_hour.setdefault(hour, {"bookings": 0, "revenue": 0.0})
        bucket["bookings"] += 1
        bucket["revenue"] += b.total_price

    revenue_by_day = []
    current_date = start_date
    while current_date <= end_date:
        date_key = current_date.strftime("%Y-%m-%d")
        revenue_by_day.append({"date": date_key, "revenue": by_day.get(date_key, 0.0)})
        current_date += timedelta(days=1)

    paid_revenue = db.query(func.sum(Payment.amount)).join(Booking).filter(
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
        Booking.booking_date >= start_date_str,
        Booking.booking_date <= end_date_str,
        Payment.status == PaymentStatus.PAID
    ).scalar() or 0.0

    loyal_customers = db.query(
        Booking.customer_name,
        Booking.customer_phone,
        func.count(Booking.id).label("booking_count"),
        func.sum(Booking.total_price).label("total_spent")
    ).filter(
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).group_by(Booking.customer_phone, Booking.customer_name).order_by(
        func.count(Booking.id).desc(), func.sum(Booking.total_price).desc()
    ).limit(10).all()

    peak_hours = [
        {
            "hour": f"{hour}:00 - {int(hour) + 1:02d}:00",
            "bookings": values["bookings"],
            "revenue": values["revenue"]
        }
        for hour, values in sorted(by_hour.items(), key=lambda item: item[1]["bookings"], reverse=True)
    ]

    return {
        "period": period,
        "period_label": period_label,
        "total_revenue": total_amount,
        "paid_revenue": paid_revenue,
        "total_bookings": total_count,
        "bookings": booking_items,
        "revenue_by_sport": by_sport,
        "revenue_by_day": revenue_by_day,
        "peak_hours": peak_hours,
        "loyal_customers": [
            {
                "name": row.customer_name,
                "phone": row.customer_phone,
                "booking_count": row.booking_count,
                "total_spent": row.total_spent or 0.0
            }
            for row in loyal_customers
        ]
    }

@router.get("/occupancy")
def get_occupancy_report(db: Session = Depends(get_db)):
    pitches = db.query(Pitch).all()
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    result = []
    total_slots_per_pitch = 12
    total_booked_slots = 0
    for p in pitches:
        bookings_count = db.query(Booking).filter(
            Booking.pitch_id == p.id,
            Booking.booking_date == today_str,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
        ).count()
        rate = round((bookings_count / 12.0) * 100.0, 1)
        total_booked_slots += bookings_count
        result.append({
            "pitch_id": p.id,
            "pitch_name": p.name,
            "sport_type": p.sport_type.value,
            "slots_booked_today": bookings_count,
            "total_slots": 12,
            "booked_hours": bookings_count,
            "total_available_hours": total_slots_per_pitch,
            "occupancy_rate": f"{rate}%",
            "status": p.status.value
        })

    return {
        "date": today_str,
        "pitches_occupancy": result,
        "overall_occupancy_rate": round(
            (total_booked_slots / (len(pitches) * total_slots_per_pitch)) * 100.0, 1
        ) if pitches else 0.0
    }
