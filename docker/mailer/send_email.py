#!/usr/bin/env python3
"""Send Atlas test email via Yahoo SMTP."""
import os
import smtplib
import sys
from email.mime.text import MIMEText


def main() -> int:
    to_addr = sys.argv[1] if len(sys.argv) > 1 else os.getenv("ATLAS_MANAGER_EMAIL", "mohamad.j1380@yahoo.com")
    subject = sys.argv[2] if len(sys.argv) > 2 else "[اطلس] تست ایمیل"
    body = sys.argv[3] if len(sys.argv) > 3 else open(sys.argv[4], encoding="utf-8").read() if len(sys.argv) > 4 else "تست"

    host = os.getenv("SMTP_HOST", "smtp.mail.yahoo.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "mohamad.j1380@yahoo.com")
    password = os.getenv("SMTP_PASS", "")

    if not password:
        print("ERROR: SMTP_PASS not set in environment")
        return 1

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())

    print(f"EMAIL_SENT to {to_addr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
