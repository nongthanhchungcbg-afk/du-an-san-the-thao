import os
import smtplib
import socket
import ssl
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from html import escape
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
        from_email = os.getenv("SMTP_FROM") or smtp_user

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((str(Header(settings.SMTP_FROM_NAME, "utf-8")), from_email))
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
                    {escape(body_text)}
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
        smtp_phase = "kết nối"
        if smtp_user and smtp_password:
            try:
                smtp_class = smtplib.SMTP_SSL if smtp_port == 465 else smtplib.SMTP
                with smtp_class(smtp_host, smtp_port, timeout=15) as server:
                    smtp_phase = "EHLO"
                    server.ehlo()
                    if smtp_port != 465 and settings.SMTP_TLS:
                        smtp_phase = "STARTTLS"
                        server.starttls(context=ssl.create_default_context())
                        smtp_phase = "EHLO sau TLS"
                        server.ehlo()
                    smtp_phase = "xác thực tài khoản"
                    server.login(smtp_user, smtp_password)
                    smtp_phase = "gửi thư"
                    refused_recipients = server.send_message(
                        msg,
                        from_addr=from_email,
                        to_addrs=[to_email],
                    )
                    if refused_recipients:
                        raise smtplib.SMTPRecipientsRefused(refused_recipients)
                return {
                    "success": True,
                    "mode": "LIVE_SMTP",
                    "message": f"Đã gửi email thành công đến {to_email} qua SMTP!"
                }
            except (smtplib.SMTPException, OSError, ssl.SSLError, ValueError) as e:
                smtp_error = e

        outbox_path = EmailService._save_local_outbox(to_email, subject, body_text)
        if smtp_error:
            if isinstance(smtp_error, smtplib.SMTPAuthenticationError):
                clean_err = "Mật khẩu SMTP chưa chính xác. Gmail yêu cầu Mật khẩu ứng dụng 16 ký tự (App Password), không dùng mật khẩu Gmail thường."
            elif isinstance(smtp_error, (TimeoutError, socket.timeout)):
                clean_err = "Kết nối máy chủ SMTP bị quá thời gian. Vui lòng kiểm tra mạng và cổng SMTP."
            elif isinstance(smtp_error, smtplib.SMTPRecipientsRefused):
                clean_err = "Máy chủ SMTP từ chối địa chỉ email người nhận. Vui lòng kiểm tra lại email."
            elif isinstance(smtp_error, smtplib.SMTPServerDisconnected):
                if smtp_phase == "xác thực tài khoản":
                    clean_err = (
                        "Gmail đã đóng kết nối ở bước xác thực tài khoản. "
                        "Email gửi và Mật khẩu ứng dụng có thể không cùng một tài khoản, "
                        "hoặc App Password đã bị thu hồi. Hãy tạo App Password mới trong đúng tài khoản Gmail."
                    )
                else:
                    clean_err = (
                        f"Máy chủ SMTP đã đóng kết nối ở bước {smtp_phase}. "
                        "Kiểm tra lại cấu hình cổng và mạng/firewall."
                    )
            elif isinstance(smtp_error, (ssl.SSLError, smtplib.SMTPConnectError, socket.gaierror)):
                clean_err = "Không thể kết nối SMTP an toàn. Vui lòng kiểm tra máy chủ, cổng và kết nối mạng."
            else:
                clean_err = f"Lỗi SMTP: {str(smtp_error)[:120]}"

            file_name = os.path.basename(outbox_path)
            return {
                "success": False,
                "mode": "SMTP_ERROR",
                "recipient": to_email,
                "subject": subject,
                "outbox_path": outbox_path,
                "message": f"{clean_err} Thư CHƯA được gửi; bản nháp đã lưu trong Hộp thư hệ thống ({file_name})."
            }

        return {
            "success": False,
            "mode": "LOCAL_OUTBOX",
            "recipient": to_email,
            "subject": subject,
            "outbox_path": outbox_path,
            "message": "Email CHƯA được gửi vì chưa cấu hình SMTP. Bản nháp đã lưu trong Hộp thư hệ thống; hãy cấu hình Gmail App Password để gửi thật."
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
