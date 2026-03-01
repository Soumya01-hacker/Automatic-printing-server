"""
=============================================================
  AutoPrint Server - Job Logger
  Records every print job to a structured CSV log.
=============================================================
"""

import csv
import os
from datetime import datetime

from config.config import LOG_DIR
from scripts.logger import logger

JOB_LOG_FILE = os.path.join(LOG_DIR, "print_jobs.csv")
_HEADERS = ["timestamp", "filename", "pages", "page_size", "status", "notes"]


def _ensure_csv() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.isfile(JOB_LOG_FILE):
        with open(JOB_LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(_HEADERS)


def log_job(
    filename: str,
    pages: int,
    page_size: str,
    status: str,
    notes: str = "",
) -> None:
    """Append one row to the print_jobs CSV and emit a logger entry."""
    _ensure_csv()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, filename, pages, page_size, status, notes]
    try:
        with open(JOB_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception as exc:
        logger.error("Failed to write job log: %s", exc)

    level = "info" if status.lower() == "success" else "error"
    getattr(logger, level)(
        "JOB | %s | file=%s | pages=%s | size=%s | notes=%s",
        status.upper(), filename, pages, page_size, notes or "-",
    )
