import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_mail(subject, body):
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_USER") or os.getenv("MAIL_TO")
    msg["To"] = os.getenv("MAIL_TO")
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")), timeout=30) as s:
        s.starttls()
        if os.getenv("SMTP_USER"):
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        s.send_message(msg)
