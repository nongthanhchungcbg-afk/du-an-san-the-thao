from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Booking, Pitch, Payment, BookingStatus, PitchType

router = APIRouter(prefix="/api/stats", tags=["Thống kê & Báo cáo"])

@router.get("/dashboard")
def get_dashboard_statistics(db: Session = Depends(get_db)):
    total_pitches = db.query(Pitch).count()
    total_bookings = db.query(Booking).count()
    confirmed_bookings = db.query(Booking).filter(Booking.status == BookingStatus.CONFIRMED).count()
    
    total_revenue = db.query(func.sum(Booking.total_price)).filter(
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).scalar() or 0.0
    
    # Tính công suất theo các môn
    football_count = db.query(Booking).join(Pitch).filter(Pitch.sport_type == PitchType.FOOTBALL).count()
    badminton_count = db.query(Booking).join(Pitch).filter(Pitch.sport_type == PitchType.BADMINTON).count()
    tennis_count = db.query(Booking).join(Pitch).filter(Pitch.sport_type == PitchType.TENNIS).count()
    gym_count = db.query(Booking).join(Pitch).filter(Pitch.sport_type == PitchType.GYM).count()
    basketball_count = db.query(Booking).join(Pitch).filter(Pitch.sport_type == PitchType.BASKETBALL).count()

    # Doanh thu 7 ngày gần nhất cho biểu đồ Chart.js
    daily_stats = []
    today = datetime.utcnow().date()
    for i in range(6, -1, -1):
        target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        day_rev = db.query(func.sum(Booking.total_price)).filter(
            Booking.booking_date == target_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
        ).scalar() or 0.0
        day_bookings = db.query(Booking).filter(Booking.booking_date == target_date).count()
        daily_stats.append({
            "date": target_date,
            "revenue": day_rev,
            "bookings": day_bookings
        })

    total_slots = (total_pitches or 1) * 12
    booked_today = db.query(Booking).filter(
        Booking.booking_date == datetime.utcnow().strftime("%Y-%m-%d"),
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).count()
    occupancy_rate = min(100.0, round((booked_today / total_slots) * 100.0, 1))

    return {
        "total_pitches": total_pitches,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "total_revenue": total_revenue,
        "occupancy_rate": occupancy_rate,
        "sports_distribution": {
            "football": football_count,
            "badminton": badminton_count,
            "tennis": tennis_count,
            "gym": gym_count,
            "basketball": basketball_count
        },
        "daily_stats": daily_stats
    }
