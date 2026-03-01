"""
=============================================================
  AutoPrint Pro — Email Handler
  Downloads attachments AND captures email body text
  for command parsing.
=============================================================
"""

import email
import imaplib
import os
import time
from email.header import decode_header
from pathlib import Path
from typing import List, Tuple

from config.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_SENDERS,
    DOWNLOAD_DIR,
    EMAIL_ADDRESS,
    EMAIL_APP_PASSWORD,
    IMAP_PORT,
    IMAP_SERVER,
)
from scripts.logger import logger


def _decode_mime_words(s: str) -> str:
    parts = decode_header(s)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(str(part))
    return "".join(decoded)


def _safe_filename(name: str) -> str:
    keep = " ._-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(c if c in keep else "_" for c in name).strip()


def _extract_body(msg) -> str:
    """Extract plain text body from email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    pass
    else:
        if msg.get_content_type() == "text/plain":
            try:
                body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )
            except Exception:
                pass
    return body.strip()


def connect_imap() -> imaplib.IMAP4_SSL:
    logger.info("Connecting to IMAP server %s:%s", IMAP_SERVER, IMAP_PORT)
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
    logger.info("IMAP login successful as %s", EMAIL_ADDRESS)
    return mail


def fetch_unseen_from_senders(mail: imaplib.IMAP4_SSL) -> List[bytes]:
    mail.select("inbox")
    all_uids = []
    for sender in ALLOWED_SENDERS:
        status, data = mail.search(None, f'(UNSEEN FROM "{sender}")')
        if status == "OK" and data[0]:
            uids = data[0].split()
            logger.info("Found %d unseen message(s) from %s", len(uids), sender)
            all_uids.extend(uids)
    if not all_uids:
        logger.info("No new messages from any allowed sender.")
    return all_uids


def download_attachments(
    mail: imaplib.IMAP4_SSL, uid: bytes
) -> List[Tuple[str, str, str]]:
    """
    Download attachments from one email.
    Returns list of (file_path, filename, email_body).
    """
    results = []
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    status, msg_data = mail.fetch(uid, "(RFC822)")
    if status != "OK":
        logger.error("Failed to fetch message UID %s", uid)
        return results

    raw_email = msg_data[0][1]
    msg       = email.message_from_bytes(raw_email)
    subject   = _decode_mime_words(msg.get("Subject", "(no subject)"))
    sender    = msg.get("From", "")
    body      = _extract_body(msg)

    logger.info("Email | Subject: %s | From: %s", subject, sender)
    if body:
        logger.info("Email body: %s", body[:100].replace("\n", " "))

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" not in content_disposition.lower():
            continue

        filename = part.get_filename()
        if not filename:
            continue

        filename = _decode_mime_words(filename)
        ext      = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.info("Skipping unsupported type: %s", filename)
            continue

        safe_name = _safe_filename(filename)
        timestamp = int(time.time())
        dest_path = os.path.join(DOWNLOAD_DIR, f"{timestamp}_{safe_name}")

        try:
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            with open(dest_path, "wb") as f:
                f.write(payload)
            logger.info("Downloaded: %s", dest_path)
            import re as _re
            _from = msg.get("From", "")
            _m = _re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', _from)
            sender_clean = _m.group(0) if _m else _from
            results.append((dest_path, filename, body, sender_clean))
        except Exception as exc:
            logger.error("Error saving %s: %s", filename, exc)

    return results


def mark_as_seen(mail: imaplib.IMAP4_SSL, uid: bytes) -> None:
    mail.store(uid, "+FLAGS", "\\Seen")


def poll_inbox() -> List[Tuple[str, str, str]]:
    """
    Returns list of (file_path, filename, email_body) tuples.
    """
    results = []
    mail    = None
    try:
        mail = connect_imap()
        uids = fetch_unseen_from_senders(mail)
        for uid in uids:
            items = download_attachments(mail, uid)
            results.extend(items)
            mark_as_seen(mail, uid)
    except imaplib.IMAP4.error as exc:
        logger.error("IMAP error: %s", exc)
    except OSError as exc:
        logger.error("Network/IO error: %s", exc)
    finally:
        if mail:
            try:
                mail.logout()
            except Exception:
                pass
    return results
