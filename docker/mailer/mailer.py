#!/usr/bin/env python3
"""HTTP mailer for Atlas Call Intelligence — relays panel/n8n emails over SMTP."""
import json
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mail.yahoo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER
DEFAULT_TO = os.getenv("ATLAS_MANAGER_EMAIL", "")
PORT = int(os.getenv("MAILER_PORT", "8765"))


def _recipients(to: str) -> list[str]:
    return [a.strip() for a in to.replace("،", ",").replace(";", ",").split(",") if a.strip()]


def send_email(to: str, subject: str, body: str, html: str = "", from_name: str = "") -> dict:
    if not SMTP_PASS:
        return {"success": False, "error": "SMTP_PASS not configured"}
    rcpts = _recipients(to)
    if not rcpts:
        return {"success": False, "error": "no recipients"}

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((str(Header(from_name, "utf-8")), SMTP_FROM)) if from_name else SMTP_FROM
    msg["To"] = ", ".join(rcpts)
    msg["Subject"] = str(Header(subject, "utf-8"))
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=SMTP_FROM.split("@")[-1] or None)
    msg.attach(MIMEText(body or " ", "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))
    raw = msg.as_string()

    errors = []
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, rcpts, raw)
        return {"success": True, "method": "smtp-starttls", "to": rcpts}
    except Exception as exc:
        errors.append(f"{SMTP_PORT}/starttls: {exc}")

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, rcpts, raw)
        return {"success": True, "method": "smtp-ssl-465", "to": rcpts}
    except Exception as exc:
        errors.append(f"465/ssl: {exc}")
        return {"success": False, "error": " | ".join(errors)}


class Handler(BaseHTTPRequestHandler):
    def _reply(self, status: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._reply(200, {"status": "ok", "smtp_configured": bool(SMTP_PASS)})
        else:
            self._reply(404, {"success": False, "error": "not found"})

    def do_POST(self):
        if self.path not in ("/send", "/"):
            self._reply(404, {"success": False, "error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8") if length else "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._reply(400, {"success": False, "error": "invalid json"})
            return

        try:
            result = send_email(
                data.get("to") or DEFAULT_TO,
                data.get("subject") or "Atlas Notification",
                data.get("body") or data.get("message") or "",
                data.get("html") or "",
                data.get("from_name") or "",
            )
        except Exception as exc:
            result = {"success": False, "error": str(exc)}
        self._reply(200 if result.get("success") else 500, result)

    def log_message(self, format, *args):
        print(format % args, flush=True)


if __name__ == "__main__":
    print(f"Atlas mailer on :{PORT} | SMTP user: {SMTP_USER} | pass configured: {bool(SMTP_PASS)}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
