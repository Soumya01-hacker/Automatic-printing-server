"""
=============================================================
  AutoPrint Pro — Configuration File
  
  SETUP INSTRUCTIONS:
  1. Copy this file and rename it to: config.py
  2. Fill in your own Gmail, printer name etc.
  3. Save and run the server!
=============================================================
"""

import os

# ── YOUR GMAIL SETTINGS ──────────────────────────────────────
# This is the Gmail account that will RECEIVE emails and trigger printing
# Create a dedicated Gmail account for this (recommended)
EMAIL_ADDRESS      = "your_print_server@gmail.com"

# Gmail App Password (NOT your regular Gmail password)
# How to get App Password:
# 1. Go to myaccount.google.com
# 2. Security → 2-Step Verification → App Passwords
# 3. Create new app password → copy the 16 character code
# 4. Paste it here (with spaces is fine e.g. "xxxx xxxx xxxx xxxx")
EMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"

# List of email addresses ALLOWED to send print jobs
# Only emails from these addresses will be printed
# Add as many as you need
ALLOWED_SENDERS = [
    "your_email@gmail.com",
    "another_allowed@gmail.com",
]

# ── YOUR PRINTER SETTINGS ────────────────────────────────────
# Exact name of your printer as shown in Windows
# To find: Open CMD and run:
# python -c "import win32print; [print(p[2]) for p in win32print.EnumPrinters(2)]"
PRINTER_NAME = "Your Printer Name Here"

# ── SERVER SETTINGS ──────────────────────────────────────────
# How often to check for new emails (in seconds)
# 15 = check every 15 seconds (recommended)
# 30 = check every 30 seconds
CHECK_INTERVAL_SEC = 15

# ── DEFAULT PRINT SETTINGS ───────────────────────────────────
# These are used when no command is given in email body
DEFAULT_PAGE_SIZE   = "A4"       # A4, A3, A5, B5, LETTER
DEFAULT_COLOR_MODE  = "colour"   # colour or bw
DEFAULT_COPIES      = 1
DEFAULT_ORIENTATION = "portrait" # portrait or landscape

# ── LIC RECEIPT SETTINGS ─────────────────────────────────────
# Documents detected as LIC receipts use these settings automatically
LIC_PAGE_SIZE  = "B5"
LIC_COLOR_MODE = "colour"
LIC_COPIES     = 1

# ── DO NOT CHANGE BELOW THIS LINE ────────────────────────────
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT   = 993

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR  = os.path.join(BASE_DIR, "downloads")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
LOG_DIR       = os.path.join(BASE_DIR, "logs")

ALLOWED_EXTENSIONS  = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_PAGES_PER_EMAIL = 25

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OCR_LANGUAGE  = "eng"

CONTRAST_FACTOR  = 1.3
SHARPNESS_FACTOR = 1.2

LOG_LEVEL        = "INFO"
LOG_ROTATION     = "midnight"
LOG_BACKUP_COUNT = 30

LIC_KEYWORDS = [
    "life insurance corporation", "lic of india", "lic premium",
    "premium receipt", "premium collection", "policy no",
    "policy number", "sum assured", "agent code", "proposal form", "lic",
]

DOCUMENT_TYPES = {
    "aadhaar": ["aadhaar", "aadhar", "uidai", "unique identification"],
    "pan": ["permanent account number", "pan card", "income tax department"],
    "birth_certificate": ["birth certificate", "date of birth", "municipal corporation"],
    "death_certificate": ["death certificate", "date of death", "cause of death"],
    "passport": ["passport", "republic of india", "ministry of external affairs"],
    "voter_id": ["election commission", "voter id", "epic no"],
    "bank_statement": ["bank statement", "account number", "ifsc"],
    "lic_receipt": LIC_KEYWORDS,
}
