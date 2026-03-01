"""
=============================================================
  AutoPrint Pro — Smart Document Detector
  Identifies document type and decides print settings.
=============================================================
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from config.config import (
    DEFAULT_COLOR_MODE,
    DEFAULT_COPIES,
    DEFAULT_ORIENTATION,
    DEFAULT_PAGE_SIZE,
    DOCUMENT_TYPES,
    LIC_COLOR_MODE,
    LIC_COPIES,
    LIC_KEYWORDS,
    LIC_PAGE_SIZE,
    OCR_LANGUAGE,
    TESSERACT_CMD,
)
from scripts.command_parser import PrintCommand
from scripts.logger import logger

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


@dataclass
class DocumentInfo:
    """Complete information about a detected document."""
    doc_type:    str          # aadhaar, pan, lic_receipt, unknown etc.
    is_lic:      bool         # True if LIC premium receipt
    print_cmd:   PrintCommand # Final resolved print settings
    needs_ocr:   bool         # Does it need OCR?
    text:        str          # Extracted text


def _extract_text_from_pdf(path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    text = ""
    try:
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text("text")
    except Exception as exc:
        logger.warning("PDF text extraction failed: %s", exc)
    return text


def _extract_text_from_image(path: str) -> str:
    """Extract text from image using Tesseract OCR."""
    try:
        with Image.open(path) as img:
            return pytesseract.image_to_string(img, lang=OCR_LANGUAGE)
    except Exception as exc:
        logger.warning("Image OCR failed: %s", exc)
        return ""


def _detect_type_from_text(text: str) -> str:
    """Match text against known document type keywords."""
    text_lower = text.lower()
    for doc_type, keywords in DOCUMENT_TYPES.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                logger.info("Document type detected: %s (keyword: %s)", doc_type, kw)
                return doc_type
    return "unknown"


def _is_lic_receipt(text: str) -> bool:
    """Returns True if the document is a LIC premium receipt."""
    text_lower = text.lower()
    matches = sum(1 for kw in LIC_KEYWORDS if kw.lower() in text_lower)
    # Need at least 2 LIC keywords to be sure
    return matches >= 2


def _needs_ocr(text: str) -> bool:
    """Returns True if document has too little text (scanned image)."""
    return len(text.strip()) < 50


def detect_document(file_path: str, email_command: PrintCommand) -> DocumentInfo:
    """
    Main detection function.
    Analyses the document and returns complete DocumentInfo
    with final resolved print settings.
    """
    ext      = Path(file_path).suffix.lower()
    text     = ""
    need_ocr = False

    # ── Extract text ─────────────────────────────────────────
    if ext == ".pdf":
        text = _extract_text_from_pdf(file_path)
        if _needs_ocr(text):
            need_ocr = True
            logger.info("PDF appears scanned — OCR will be needed")
    elif ext in {".jpg", ".jpeg", ".png"}:
        text     = _extract_text_from_image(file_path)
        need_ocr = True  # Images always go through processing

    # ── Detect document type ──────────────────────────────────
    doc_type = _detect_type_from_text(text)
    is_lic   = (doc_type == "lic_receipt") or _is_lic_receipt(text)

    # ── Resolve final print settings ─────────────────────────
    # Priority: Email Command > LIC Default > Global Default

    if email_command.has_command:
        # Email command overrides EVERYTHING
        final_cmd = PrintCommand(
            page_size   = email_command.page_size,
            color_mode  = email_command.color_mode,
            copies      = email_command.copies,
            orientation = email_command.orientation,
            has_command = True,
        )
        logger.info(
            "Print settings from EMAIL COMMAND: size=%s colour=%s copies=%d orient=%s",
            final_cmd.page_size, final_cmd.color_mode,
            final_cmd.copies, final_cmd.orientation,
        )
    elif is_lic:
        # LIC receipt defaults
        final_cmd = PrintCommand(
            page_size   = LIC_PAGE_SIZE,
            color_mode  = LIC_COLOR_MODE,
            copies      = LIC_COPIES,
            orientation = DEFAULT_ORIENTATION,
            has_command = False,
        )
        logger.info("Print settings from LIC DEFAULT: B5 Colour")
    else:
        # Global defaults
        final_cmd = PrintCommand(
            page_size   = DEFAULT_PAGE_SIZE,
            color_mode  = DEFAULT_COLOR_MODE,
            copies      = DEFAULT_COPIES,
            orientation = DEFAULT_ORIENTATION,
            has_command = False,
        )
        logger.info(
            "Print settings from GLOBAL DEFAULT: %s %s",
            final_cmd.page_size, final_cmd.color_mode,
        )

    return DocumentInfo(
        doc_type  = doc_type,
        is_lic    = is_lic,
        print_cmd = final_cmd,
        needs_ocr = need_ocr,
        text      = text,
    )
