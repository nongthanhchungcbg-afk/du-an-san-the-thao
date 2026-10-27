import os
from datetime import datetime, timedelta
from app.database import engine, Base, SessionLocal
from app.models import (
    User, Pitch, Booking, Payment, Maintenance, Review, MatchPost, EventAnnouncement,
    UserRole, PitchType, PitchStatus, BookingStatus, PaymentType, PaymentMethod, PaymentStatus, MaintenanceStatus,
    Customer, CourtType, Price, TimeSlot
)
from app.auth import get_password_hash

def seed():
    print("Dang khoi tao bang du lieu CSDL...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Kiem tra va tao nguoi dung
    db.query(User).delete()
    print("-> Khoi tao nguoi dung chinh chu (Nhom 03 ICTU)...")
    users = [
        User(
            username="admin",
            email="thanhchung.ictu@gmail.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Nông Thành Chung",
            phone="0816227206",
            role=UserRole.ADMIN
        ),
        User(
            username="thanhchung",
            email="nongthanhchung@ictu.edu.vn",
            hashed_password=get_password_hash("chung123"),
            full_name="Nông Thành Chung (Nhóm Trưởng)",
            phone="0816227206",
            role=UserRole.ADMIN
        ),
        User(
            username="nhanvien",
            email="locnguyen@thethaoictu.vn",
            hashed_password=get_password_hash("staff123"),
            full_name="Nguyễn Văn Lộc",
            phone="0977234567",
            role=UserRole.STAFF
        ),
        User(
            username="hoangtrituong",
            email="tuonghoang@thethaoictu.vn",
            hashed_password=get_password_hash("tuong123"),
            full_name="Hoàng Trí Tường",
            phone="0988654321",
            role=UserRole.STAFF
        ),
        User(
            username="khachhang",
            email="hungnguyen@gmail.com",
            hashed_password=get_password_hash("user123"),
            full_name="Nguyễn Văn Hùng",
            phone="0912345678",
            role=UserRole.CUSTOMER
        )
    ]
    db.add_all(users)
    db.commit()

    # 2. Tao danh sach 8 san the thao da dang & dia diem
    db.query(Pitch).delete()
    print("-> Khoi tao danh sach 8 san the thao...")
    pitches = [
        Pitch(
            name="Sân 1: Sân Bóng Đá Mini A1 (Cỏ Nhân Tạo 5 Người)",
            sport_type=PitchType.FOOTBALL,
            location="Cơ sở 1: 128 Đường Z115, Tân Thịnh, TP. Thái Nguyên",
            price_per_hour=250000,
            peak_price_per_hour=350000,
            status=PitchStatus.AVAILABLE,
            description="Mặt cỏ FIFA Pro êm ái, hệ thống chiếu sáng đèn LED 400W hiện đại, miễn phí nước suối và áo bib thi đấu.",
            image_url="/static/images/pitch-01.jpg"
        ),
        Pitch(
            name="Sân 2: Sân Bóng Đá Tiêu Chuẩn A2 (Cỏ 7 Người)",
            sport_type=PitchType.FOOTBALL,
            location="Cơ sở 1: 128 Đường Z115, Tân Thịnh, TP. Thái Nguyên",
            price_per_hour=400000,
            peak_price_per_hour=550000,
            status=PitchStatus.AVAILABLE,
            description="Sân rộng đạt chuẩn thi đấu giải phong trào, có khán đài mini và bình luận viên hỗ trợ.",
            image_url="/static/images/pitch-02.jpg"
        ),
        Pitch(
            name="Sân 3: Sân Cầu Lông Thi Đấu VIP 1",
            sport_type=PitchType.BADMINTON,
            location="Cơ sở 1: Nhà Thi Đấu Trung Tâm Z115 (Tầng 1)",
            price_per_hour=80000,
            peak_price_per_hour=120000,
            status=PitchStatus.AVAILABLE,
            description="Thảm cao cấp Yonex 5 lớp chống trượt, trần cao 9m thoáng đãng, đèn chuyên dụng chống lóa mắt.",
            image_url="/static/images/pitch-03.jpg"
        ),
        Pitch(
            name="Sân 4: Sân Cầu Lông Tiêu Chuẩn 2",
            sport_type=PitchType.BADMINTON,
            location="Cơ sở 1: Nhà Thi Đấu Trung Tâm Z115 (Tầng 1)",
            price_per_hour=70000,
            peak_price_per_hour=100000,
            status=PitchStatus.AVAILABLE,
            description="Sân tập luyện thể lực hàng ngày, trang bị ghế nghỉ ngơi và quạt trần công nghiệp làm mát cực tốt.",
            image_url="/static/images/pitch-04.jpg"
        ),
        Pitch(
            name="Sân 5: Sân Tennis Đất Nện Quốc Tế T1",
            sport_type=PitchType.TENNIS,
            location="Cơ sở 2: Khu Phức Hợp Thể Thao Quyết Thắng, TP. Thái Nguyên",
            price_per_hour=180000,
            peak_price_per_hour=280000,
            status=PitchStatus.AVAILABLE,
            description="Mặt sân đất nện chuẩn Roland Garros, giảm chấn động khớp gối và cột sống cho người chơi thể thao.",
            image_url="/static/images/pitch-05.jpg"
        ),
        Pitch(
            name="Sân 6: Sân Tennis Mặt Cứng US Open T2",
            sport_type=PitchType.TENNIS,
            location="Cơ sở 2: Khu Phức Hợp Thể Thao Quyết Thắng, TP. Thái Nguyên",
            price_per_hour=170000,
            peak_price_per_hour=260000,
            status=PitchStatus.AVAILABLE,
            description="Mặt sân Acrylic 8 lớp phẳng tuyệt đối, độ nảy bóng cực chuẩn cho vận động viên và người chơi nâng cao.",
            image_url="/static/images/pitch-06.jpg"
        ),
        Pitch(
            name="Sân 7: Khu Rèn Luyện Thể Hình Pro Gym & Fitness",
            sport_type=PitchType.GYM,
            location="Cơ sở 1: 128 Đường Z115 (Tầng 2), Tân Thịnh, TP. Thái Nguyên",
            price_per_hour=50000,
            peak_price_per_hour=70000,
            status=PitchStatus.AVAILABLE,
            description="Hệ thống máy tập tạ đa năng, máy chạy bộ, khu vực tạ tay Dumbbell & Squat rack chuyên sâu phát triển cơ bắp.",
            image_url="/static/images/pitch-07.jpg"
        ),
        Pitch(
            name="Sân 8: Sân Bóng Rổ & Thể Thao Đa Năng",
            sport_type=PitchType.BASKETBALL,
            location="Cơ sở 2: Khu Phức Hợp Thể Thao Quyết Thắng, TP. Thái Nguyên",
            price_per_hour=150000,
            peak_price_per_hour=220000,
            status=PitchStatus.AVAILABLE,
            description="Trụ bóng rổ kính cường lực lò xo giảm chấn, vạch kẻ thi đấu sắc nét, phục vụ tập luyện và thi đấu 3x3, 5x5.",
            image_url="/static/images/pitch-08.jpg"
        )
    ]
    db.add_all(pitches)
    db.commit()

    # 3. Tao danh gia mau
    db.query(Review).delete()
    reviews = [
        Review(
            customer_name="Trần Văn Minh (FC Bách Khoa)",
            rating=5,
            comment="Sân bóng cỏ nhân tạo ở cơ sở 1 đá cực êm chân, ánh sáng đèn đêm rất sáng và không bị chói mắt! Ban quản lý nhiệt tình."
        ),
        Review(
            customer_name="Nguyễn Phương Thảo",
            rating=5,
            comment="Sân cầu lông VIP thảm Yonex độ bám rất tốt, có phòng thay đồ và quầy nước sạch sẽ. Rất thích đặt lịch qua web vì không bị trùng giờ."
        ),
        Review(
            customer_name="Hoàng Nam - CLB Tennis Thái Nguyên",
            rating=5,
            comment="Mặt sân đất nện rất hiếm có ở Thái Nguyên, chơi cực đã! Trợ lý AI trả lời nhanh và báo đúng khung giờ trống."
        )
    ]
    db.add_all(reviews)
    db.commit()

    # 4. Tao bai dang giao luu mau
    db.query(MatchPost).delete()
    matches = [
        MatchPost(
            author_name="FC Xây Dựng & Kiến Trúc",
            sport_type=PitchType.FOOTBALL,
            team_level="Phong trào vui vẻ / U30",
            match_time="18h00 Thứ Sáu tuần này (21/08)",
            contact_phone="0816227206",
            content="Cần tìm 1 đội bóng đá 7 người giao lưu cọ xát cuối tuần, chia tiền sân 5-5, có nước nôi giao lưu sau trận."
        ),
        MatchPost(
            author_name="CLB Cầu Lông Trẻ ICTU",
            sport_type=PitchType.BADMINTON,
            team_level="Trình độ Trung bình - Khá",
            match_time="17h30 Chiều Thứ Bảy",
            contact_phone="0912345678",
            content="Tìm 2 bạn đánh đôi nam hoặc đôi nam nữ giao lưu vui vẻ nâng cao tay nghề, sân đã đặt sẵn ở cơ sở 1."
        )
    ]
    db.add_all(matches)
    db.commit()

    # 5. Tao thong bao su kien mau
    db.query(EventAnnouncement).delete()
    events = [
        EventAnnouncement(
            title="🏆 Giải Bóng Đá Tứ Hùng Sinh Viên ICTU 2026",
            category="GIẢI ĐẤU",
            description="Khai mạc giải đấu thường niên quy tụ 8 đội bóng phong trào xuất sắc nhất TP. Thái Nguyên. Tổng giải thưởng lên tới 15.000.000 VNĐ.",
            event_date="Từ 25/08/2026 đến 30/08/2026",
            banner_url="/static/images/pitch-01.jpg"
        ),
        EventAnnouncement(
            title="⚡ Khuyến Mãi Giờ Vàng: Giảm 20% Khung Giờ Sáng (06:00 - 09:00)",
            category="KHUYẾN MÃI",
            description="Khuyến khích rèn luyện thể lực buổi sáng, tất cả các sân cầu lông và bóng đá giảm ngay 20% khi đặt sân trực tuyến trên hệ thống.",
            event_date="Áp dụng từ thứ 2 đến thứ 6 hàng tuần",
            banner_url="/static/images/pitch-02.jpg"
        )
    ]
    db.add_all(events)
    db.commit()

    # 6. Tao khach hang mau (Table 2.4 Word doc)
    print("-> Khoi tao danh sach khach hang mau...")
    db.query(Customer).delete()
    customers = [
        Customer(name="Nông Thành Chung", phone="0816227206", email="nongthanhchungcbg@gmail.com", address="Bắc Giang"),
        Customer(name="Nguyễn Văn Hùng", phone="0911223344", email="hungnguyen@gmail.com", address="Thái Nguyên"),
        Customer(name="Trần Văn Minh", phone="0933445566", email="minhfc@gmail.com", address="Hà Nội"),
        Customer(name="Nguyễn Phương Thảo", phone="0978112233", email="thaonp@gmail.com", address="Thái Nguyên"),
        Customer(name="Hoàng Nam", phone="0905556677", email="namclb@gmail.com", address="Thái Nguyên")
    ]
    db.add_all(customers)
    db.commit()

    # 7. Tao loai san va bang gia gio (Table 2.5 Word doc)
    print("-> Khoi tao loai san va bang gia gio...")
    db.query(Price).delete()
    db.query(CourtType).delete()
    court_types = [
        CourtType(id=1, name="Sân bóng đá cỏ nhân tạo", sport_type="FOOTBALL", description="Sân 5-7 người tiêu chuẩn"),
        CourtType(id=2, name="Sân cầu lông thảm Yonex", sport_type="BADMINTON", description="Thảm chuyên dụng chống trơn trượt"),
        CourtType(id=3, name="Sân Tennis quốc tế", sport_type="TENNIS", description="Mặt sân đất nện và cứng"),
        CourtType(id=4, name="Sân bóng rổ & Gym", sport_type="BASKETBALL", description="Sân bóng rổ tiêu chuẩn")
    ]
    db.add_all(court_types)
    db.commit()

    prices = [
        Price(court_type_id=1, day_of_week="ALL", start_time="06:00", end_time="17:00", price=250000),
        Price(court_type_id=1, day_of_week="ALL", start_time="17:00", end_time="22:00", price=350000),
        Price(court_type_id=2, day_of_week="ALL", start_time="06:00", end_time="17:00", price=70000),
        Price(court_type_id=2, day_of_week="ALL", start_time="17:00", end_time="22:00", price=120000),
        Price(court_type_id=3, day_of_week="ALL", start_time="06:00", end_time="17:00", price=180000),
        Price(court_type_id=3, day_of_week="ALL", start_time="17:00", end_time="22:00", price=280000),
        Price(court_type_id=4, day_of_week="ALL", start_time="06:00", end_time="22:00", price=150000)
    ]
    db.add_all(prices)
    db.commit()

    # 8. Tao lich trinh bao tri mau (Table 2.10 Word doc & Image 4)
    print("-> Khoi tao lich trinh bao tri mau...")
    db.query(Maintenance).delete()
    today_str = datetime.now().strftime("%Y-%m-%d")
    d1 = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    d2 = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    d3 = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    d4 = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")

    maintenances = [
        Maintenance(
            pitch_id=1,
            start_date=d1,
            end_date=d2,
            reason="Bảo dưỡng chải hạt cao su & kiểm tra thảm cỏ nhân tạo",
            cost=1500000,
            status=MaintenanceStatus.DONE
        ),
        Maintenance(
            pitch_id=2,
            start_date=today_str,
            end_date=d3,
            reason="Thay dàn bóng đèn cao áp LED Philips 400W cột số 2",
            cost=3200000,
            status=MaintenanceStatus.IN_PROGRESS
        ),
        Maintenance(
            pitch_id=3,
            start_date=d3,
            end_date=d4,
            reason="Căng lại hệ thống lưới bao và kẻ lại vạch thi đấu Yonex",
            cost=850000,
            status=MaintenanceStatus.SCHEDULED
        )
    ]
    db.add_all(maintenances)
    db.commit()

    # 9. Tao don dat san & thanh toan mau (Table 2.7 & Table 2.8 Word doc)
    print("-> Khoi tao don dat san & thanh toan mau...")
    db.query(Payment).delete()
    db.query(Booking).delete()
    
    b1 = Booking(
        user_id=1,
        customer_id=1,
        pitch_id=1,
        customer_name="Nông Thành Chung",
        customer_phone="0816227206",
        booking_date=today_str,
        start_time="17:00",
        end_time="19:00",
        total_price=700000,
        deposit_amount=200000,
        payment_method=PaymentMethod.BANK_TRANSFER,
        payment_status=PaymentStatus.PAID,
        bank_name="MB",
        status=BookingStatus.CONFIRMED,
        note="Giao lưu đội bóng cựu sinh viên ICTU",
        invoice_sent=True,
        invoice_email="nongthanhchungcbg@gmail.com"
    )
    b2 = Booking(
        user_id=5,
        customer_id=2,
        pitch_id=3,
        customer_name="Nguyễn Văn Hùng",
        customer_phone="0911223344",
        booking_date=today_str,
        start_time="18:00",
        end_time="20:00",
        total_price=240000,
        deposit_amount=100000,
        payment_method=PaymentMethod.WALLET,
        payment_status=PaymentStatus.PAID,
        bank_name="MB",
        status=BookingStatus.CONFIRMED,
        note="Đánh đôi cầu lông",
        invoice_sent=True,
        invoice_email="hungnguyen@gmail.com"
    )
    b3 = Booking(
        user_id=5,
        customer_id=3,
        pitch_id=5,
        customer_name="Trần Văn Minh",
        customer_phone="0933445566",
        booking_date=today_str,
        start_time="07:00",
        end_time="09:00",
        total_price=360000,
        deposit_amount=0,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PENDING,
        bank_name=None,
        status=BookingStatus.PENDING,
        note="Tập luyện tennis buổi sáng",
        invoice_sent=False,
        invoice_email="minhfc@gmail.com"
    )
    db.add_all([b1, b2, b3])
    db.commit()

    p1 = Payment(
        booking_id=b1.id,
        amount=700000,
        payment_type=PaymentType.FULL_PAYMENT,
        payment_method=PaymentMethod.BANK_TRANSFER,
        status=PaymentStatus.PAID,
        transaction_ref=f"TXN{b1.id}MB123",
        bank_name="MB",
        note="Thanh toan VietQR MB Bank"
    )
    p2 = Payment(
        booking_id=b2.id,
        amount=240000,
        payment_type=PaymentType.FULL_PAYMENT,
        payment_method=PaymentMethod.WALLET,
        status=PaymentStatus.PAID,
        transaction_ref=f"TXNWL{b2.id}",
        bank_name="WALLET",
        note="Thanh toan bang so du Vi dien tu"
    )
    db.add_all([p1, p2])
    db.commit()

    db.close()
    print("[OK] Hoan tat khoi tao CSDL thanh cong!")

if __name__ == "__main__":
    seed()
