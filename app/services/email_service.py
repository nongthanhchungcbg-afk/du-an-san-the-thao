import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.config import settings


class EmailService:
    @staticmethod
    def _save_local_outbox(to_email: str, subject: str, body_text: str) -> str:
        outbox_dir = Path(__file__).resolve().parent.parent / "storage" / "email_outbox"
        outbox_dir.mkdir(parents=True, exist_ok=True)

        safe_email = str(to_email).replace("@", "_at_").replace("/", "_")
        safe_subject = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in subject[:40])
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        file_name = f"{timestamp}_{safe_email}_{safe_subject}.eml"
        file_path = outbox_dir / file_name

        payload = (
            f"To: {to_email}\n"
            f"Subject: {subject}\n"
            f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}\n\n"
            f"{body_text}\n"
        )
        file_path.write_text(payload, encoding="utf-8")
        return str(file_path)

    @staticmethod
    def send_email(to_email: str, subject: str, body_text: str, body_html: str = None) -> dict:
        smtp_host = os.getenv("SMTP_HOST", getattr(settings, "SMTP_HOST", "smtp.gmail.com"))
        smtp_port = int(os.getenv("SMTP_PORT", getattr(settings, "SMTP_PORT", 587)))
        smtp_user = os.getenv("SMTP_USER", getattr(settings, "SMTP_USER", ""))
        smtp_password = os.getenv("SMTP_PASSWORD", getattr(settings, "SMTP_PASSWORD", ""))
        from_email = os.getenv("SMTP_FROM", getattr(settings, "SMTP_FROM_EMAIL", smtp_user or "santhethao.ictu@gmail.com"))

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Hệ Thống Sân Thể Thao ICTU <{from_email}>"
        msg["To"] = to_email

        part1 = MIMEText(body_text, "plain", "utf-8")
        msg.attach(part1)

        if not body_html:
            body_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 16px; background-color: #ffffff;">
                <div style="text-align: center; border-bottom: 2px solid #10b981; padding-bottom: 12px; margin-bottom: 20px;">
                    <h2 style="color: #065f46; margin: 0;">{settings.PROJECT_NAME}</h2>
                    <p style="color: #64748b; font-size: 12px; margin: 4px 0 0 0;">Hệ Thống Đặt Sân Tự Động & Trợ Lý AI Thông Minh | Hotline: 0816227206</p>
                </div>
                <div style="color: #334155; line-height: 1.6; font-size: 14px; white-space: pre-line;">
                    {body_text}
                </div>
                <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #f1f5f9; text-align: center; font-size: 12px; color: #94a3b8;">
                    <p style="margin: 0;">Mọi thắc mắc xin liên hệ Hotline / Zalo: <strong>0816227206</strong></p>
                    <p style="margin: 4px 0 0 0;">Địa chỉ: 128 Đường Z115, Tân Thịnh, TP. Thái Nguyên</p>
                </div>
            </div>
            """
        part2 = MIMEText(body_html, "html", "utf-8")
        msg.attach(part2)

        smtp_error = None
        if smtp_user and smtp_password:
            try:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [to_email], msg.as_string())
                server.quit()
                return {
                    "success": True,
                    "mode": "LIVE_SMTP",
                    "message": f"Đã gửi email thành công đến {to_email} qua SMTP!"
                }
            except Exception as e:
                smtp_error = str(e)
                print(f"[EmailService] Lỗi SMTP: {smtp_error}")

        outbox_path = EmailService._save_local_outbox(to_email, subject, body_text)
        if smtp_error:
            if "535" in smtp_error or "Username and Password not accepted" in smtp_error:
                clean_err = "Mật khẩu SMTP chưa chính xác (Lỗi 535). Gmail yêu cầu Mật khẩu ứng dụng 16 ký tự (App Password), không dùng mật khẩu Gmail thường."
            elif "timed out" in smtp_error.lower() or "timeout" in smtp_error.lower():
                clean_err = "Kết nối máy chủ SMTP bị quá thời gian (Timeout). Vui lòng kiểm tra lại mạng hoặc cổng 587."
            else:
                clean_err = f"Lỗi gửi thư SMTP: {smtp_error[:80]}..."

            file_name = os.path.basename(outbox_path)
            print(f"[EmailService] {clean_err} Đã lưu vào outbox local tại {outbox_path}")
            return {
                "success": False,
                "mode": "SMTP_ERROR",
                "recipient": to_email,
                "subject": subject,
                "outbox_path": outbox_path,
                "message": f"{clean_err} Hệ thống đã tự động lưu thư vào Hộp thư hệ thống ({file_name})."
            }

        print(f"[EmailService] Chưa cấu hình SMTP; email đã được lưu vào local outbox: {outbox_path}")
        return {
            "success": True,
            "mode": "LOCAL_OUTBOX",
            "recipient": to_email,
            "subject": subject,
            "outbox_path": outbox_path,
            "message": "Email đã được lưu vào hộp thư local. Cấu hình SMTP Gmail App Password để gửi thật đến khách hàng."
        }

    @staticmethod
    def send_otp_reset_email(to_email: str, full_name: str, otp_code: str) -> dict:
        subject = f"[{settings.PROJECT_NAME}] Mã Xác Thực Quên Mật Khẩu (OTP)"
        body = f"""Kính gửi {full_name},

Bạn vừa yêu cầu đặt lại mật khẩu cho tài khoản trên Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI.
Mã xác thực OTP gồm 4 chữ số của bạn là:

    ==>  {otp_code}  <==

Mã này có hiệu lực trong vòng 15 phút. Tuyệt đối không chia sẻ mã này cho bất kỳ ai!
Hotline hỗ trợ: 0816227206"""
        return EmailService.send_email(to_email, subject, body)

    @staticmethod
    def send_booking_confirmation_email(booking_dict: dict, pitch_dict: dict, to_email: str) -> dict:
        subject = f"[{settings.PROJECT_NAME}] Xác Nhận Đặt Sân Thành Công #{booking_dict.get('id')}"
        body = f"""Kính gửi quý khách {booking_dict.get('customer_name')},

Đơn đặt sân của bạn đã được tiếp nhận và xác nhận thành công trên hệ thống:
- Mã đơn đặt: #{booking_dict.get('id')}
- Sân thi đấu: {pitch_dict.get('name')} ({pitch_dict.get('sport_type')})
- Địa chỉ: {pitch_dict.get('location', '128 Đường Z115, Thái Nguyên')}
- Thời gian: {booking_dict.get('start_time')} - {booking_dict.get('end_time')} ngày {booking_dict.get('booking_date')}
- Tổng tiền: {booking_dict.get('total_price', 0):,.0f} VNĐ
- Tiền cọc: {booking_dict.get('deposit_amount', 0):,.0f} VNĐ
- Hình thức: {booking_dict.get('payment_method')}

Chúc bạn có những trận đấu thể thao bùng nổ và nhiều niềm vui!
Hotline / Zalo hỗ trợ: 0816227206"""
        return EmailService.send_email(to_email, subject, body)

    @staticmethod
    def send_invoice_email(booking_dict: dict, to_email: str, invoice_data: dict = None) -> dict:
        subject = f"[{settings.PROJECT_NAME}] Hóa Đơn Điện Tử Đặt Sân #{booking_dict.get('id')}"
        body = f"""Kính gửi quý khách {booking_dict.get('customer_name')},

Hệ thống gửi đến bạn hóa đơn điện tử cho đơn đặt sân #{booking_dict.get('id')}:
- Khách hàng: {booking_dict.get('customer_name')}
- Sân thi đấu: {booking_dict.get('pitch_name', 'Sân thể thao')}
- Tổng thanh toán: {booking_dict.get('total_price', 0):,.0f} VNĐ
- Trạng thái: ĐÃ THANH TOÁN

Hotline hỗ trợ: 0816227206
Địa chỉ: 128 Đường Z115, Tân Thịnh, TP. Thái Nguyên"""
        return EmailService.send_email(to_email, subject, body)

    @staticmethod
    def get_outbox_emails() -> list:
        outbox_dir = Path(__file__).resolve().parent.parent / "storage" / "email_outbox"
        if not outbox_dir.exists():
            return []
        files = sorted(outbox_dir.glob("*.eml"), key=os.path.getmtime, reverse=True)
        results = []
        for f in files[:50]:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                results.append({
                    "filename": f.name,
                    "mtime": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "content": content
                })
            except Exception as e:
                print(f"[EmailService] Lỗi đọc eml {f}: {e}")
        return results

