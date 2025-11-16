# app/mail_alert.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_USER, GMAIL_PASS  # ✅ 從 config.py 讀取環境變數

def send_alert_email(subject, body, to_email):
    """寄送海警船警示信"""
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)

        print(f"📧 已寄出 Gmail 至 {to_email}")

    except Exception as e:
        print(f"❌ 寄信失敗: {e}")
