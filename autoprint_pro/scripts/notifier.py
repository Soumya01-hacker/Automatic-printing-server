"""
=============================================================
  AutoPrint Pro — Email Notifier
  Sends confirmation email after successful print.
=============================================================
"""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.config import EMAIL_ADDRESS, EMAIL_APP_PASSWORD
from scripts.logger import logger


def send_print_success(to: str, filename: str, pages: int,
                       page_size: str, doc_type: str, copies: int) -> None:
    """Send confirmation email to sender after successful print."""
    if not to:
        return
    now     = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    subject = f"✅ Printed Successfully — {filename}"
    html    = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:480px;margin:auto">
    <div style="background:#22c55e;padding:14px;border-radius:8px 8px 0 0;text-align:center">
        <h2 style="color:white;margin:0">✅ Print Successful!</h2>
    </div>
    <div style="border:1px solid #ddd;border-top:none;padding:20px;border-radius:0 0 8px 8px">
    <table width="100%" cellpadding="8" style="border-collapse:collapse">
        <tr style="background:#f9f9f9"><td><b>📄 File</b></td><td>{filename}</td></tr>
        <tr><td><b>📋 Type</b></td><td>{doc_type.replace('_',' ').title()}</td></tr>
        <tr style="background:#f9f9f9"><td><b>📐 Size</b></td><td>{page_size}</td></tr>
        <tr><td><b>📃 Pages</b></td><td>{pages}</td></tr>
        <tr style="background:#f9f9f9"><td><b>🔢 Copies</b></td><td>{copies}</td></tr>
        <tr><td><b>🕐 Time</b></td><td>{now}</td></tr>
    </table>
    <p style="color:#888;font-size:11px;text-align:center;margin-top:15px">
        AutoPrint Pro — Automatic Print Server
    </p>
    </div></body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"AutoPrint Pro <{EMAIL_ADDRESS}>"
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            s.sendmail(EMAIL_ADDRESS, to, msg.as_string())
        logger.info("✅ Confirmation sent to %s", to)
    except Exception as exc:
        logger.error("Notification failed: %s", exc)


def send_print_failure(to: str, filename: str, reason: str) -> None:
    """Send failure alert email to sender."""
    if not to:
        return
    now     = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    subject = f"❌ Print Failed — {filename}"
    html    = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:480px;margin:auto">
    <div style="background:#ef4444;padding:14px;border-radius:8px 8px 0 0;text-align:center">
        <h2 style="color:white;margin:0">❌ Print Failed!</h2>
    </div>
    <div style="border:1px solid #ddd;border-top:none;padding:20px;border-radius:0 0 8px 8px">
    <table width="100%" cellpadding="8" style="border-collapse:collapse">
        <tr style="background:#f9f9f9"><td><b>📄 File</b></td><td>{filename}</td></tr>
        <tr><td><b>❗ Reason</b></td><td style="color:#ef4444">{reason}</td></tr>
        <tr style="background:#f9f9f9"><td><b>🕐 Time</b></td><td>{now}</td></tr>
    </table>
    <p style="color:#555;text-align:center;margin-top:12px">
        Please check printer and resend the file.
    </p>
    <p style="color:#888;font-size:11px;text-align:center">AutoPrint Pro</p>
    </div></body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"AutoPrint Pro <{EMAIL_ADDRESS}>"
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            s.sendmail(EMAIL_ADDRESS, to, msg.as_string())
        logger.info("❌ Failure alert sent to %s", to)
    except Exception as exc:
        logger.error("Failure notification failed: %s", exc)
