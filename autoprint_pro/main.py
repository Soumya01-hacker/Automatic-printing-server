"""
=============================================================
  AutoPrint Pro — LIC Agent Edition
  Phase 1 + Auto Reply Notification

  Usage:
      python main.py          # Run continuously
      python main.py --once   # Run once and exit (for testing)
=============================================================
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.config import (
    CHECK_INTERVAL_SEC,
    DOWNLOAD_DIR,
    LOG_DIR,
    PROCESSED_DIR,
)
from scripts.command_parser import parse_email_commands
from scripts.document_detector import detect_document
from scripts.document_processor import process_document
from scripts.email_handler import poll_inbox
from scripts.job_logger import log_job
from scripts.logger import logger
from scripts.notifier import send_print_failure, send_print_success
from scripts.print_manager import print_pdf_windows


def _ensure_directories() -> None:
    for d in (DOWNLOAD_DIR, PROCESSED_DIR, LOG_DIR):
        os.makedirs(d, exist_ok=True)


def process_and_print(file_path: str, email_body: str = "",
                      sender_email: str = "") -> None:
    filename = os.path.basename(file_path)
    logger.info("━━━ Starting: %s ━━━", filename)

    # ── Step 1: Parse email commands ─────────────────────────
    email_cmd = parse_email_commands(email_body)
    if email_cmd.has_command:
        logger.info(
            "Email command: size=%s colour=%s copies=%d orient=%s",
            email_cmd.page_size, email_cmd.color_mode,
            email_cmd.copies, email_cmd.orientation,
        )
    else:
        logger.info("No email command — using auto detection")

    # ── Step 2: Detect document type ─────────────────────────
    try:
        doc_info = detect_document(file_path, email_cmd)
        logger.info(
            "Document: type=%s lic=%s → print: %s %s x%d %s",
            doc_info.doc_type, doc_info.is_lic,
            doc_info.print_cmd.page_size,
            doc_info.print_cmd.color_mode,
            doc_info.print_cmd.copies,
            doc_info.print_cmd.orientation,
        )
    except Exception as exc:
        logger.error("Detection failed for %s: %s", filename, exc)
        log_job(filename, 0, "N/A", "ERROR", str(exc))
        if sender_email:
            send_print_failure(sender_email, filename, str(exc))
        return

    # ── Step 3: Process document ──────────────────────────────
    try:
        output_pdf, page_count = process_document(file_path, doc_info)
    except Exception as exc:
        logger.error("Processing failed for %s: %s", filename, exc, exc_info=True)
        log_job(filename, 0, "N/A", "ERROR", str(exc))
        if sender_email:
            send_print_failure(sender_email, filename, "Processing failed")
        return

    # ── Step 4: Print ─────────────────────────────────────────
    copies     = doc_info.print_cmd.copies
    color_mode = doc_info.print_cmd.color_mode
    success    = print_pdf_windows(output_pdf, color_mode=color_mode, copies=copies)
    size_label = f"{doc_info.print_cmd.page_size} {doc_info.print_cmd.color_mode}"

    # ── Step 5: Log + Notify ──────────────────────────────────
    if success:
        log_job(
            filename  = filename,
            pages     = page_count,
            page_size = size_label,
            status    = "SUCCESS",
            notes     = f"type={doc_info.doc_type} copies={copies}",
        )
        logger.info("✅ Printed: %s | %s | pages=%d | copies=%d",
                    filename, size_label, page_count, copies)
        if sender_email:
            send_print_success(
                to        = sender_email,
                filename  = filename,
                pages     = page_count,
                page_size = size_label,
                doc_type  = doc_info.doc_type,
                copies    = copies,
            )
    else:
        log_job(
            filename  = filename,
            pages     = page_count,
            page_size = size_label,
            status    = "PRINT_FAILED",
            notes     = "Printer error — check printer",
        )
        if sender_email:
            send_print_failure(
                sender_email, filename,
                "Printer error — check printer is ON and has paper"
            )

    logger.info("━━━ Done: %s ━━━", filename)


def run_once() -> None:
    logger.info("Polling inbox …")
    try:
        attachments = poll_inbox()
    except Exception as exc:
        logger.error("Inbox poll failed: %s", exc, exc_info=True)
        return

    if not attachments:
        logger.info("No new attachments found.")
        return

    logger.info("Found %d attachment(s) to process.", len(attachments))
    for item in attachments:
        file_path    = item[0]
        email_body   = item[2] if len(item) > 2 else ""
        sender_email = item[3] if len(item) > 3 else ""
        process_and_print(file_path, email_body, sender_email)


def run_continuous() -> None:
    logger.info("AutoPrint Pro started. Polling every %ds.", CHECK_INTERVAL_SEC)
    logger.info("Monitoring inbox for emails from configured senders.")
    logger.info("Press Ctrl+C to stop.")

    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logger.info("Shutdown requested.")
            break
        except Exception as exc:
            logger.error("Unhandled error: %s", exc, exc_info=True)

        try:
            time.sleep(CHECK_INTERVAL_SEC)
        except KeyboardInterrupt:
            logger.info("Shutdown requested.")
            break

    logger.info("AutoPrint Pro stopped.")


if __name__ == "__main__":
    _ensure_directories()
    parser = argparse.ArgumentParser(description="AutoPrint Pro")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        run_once()
    else:
        run_continuous()
