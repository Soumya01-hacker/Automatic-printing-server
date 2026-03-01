"""
=============================================================
  AutoPrint Pro — Print Manager
  Sends PDF to printer with correct colour settings.
=============================================================
"""

import os
import subprocess

from config.config import PRINTER_NAME
from scripts.logger import logger


def _get_default_printer() -> str:
    try:
        import win32print
        return win32print.GetDefaultPrinter()
    except Exception as exc:
        logger.warning("Could not get default printer: %s", exc)
        return ""


def print_pdf_windows(
    pdf_path: str,
    color_mode: str = "colour",
    copies: int = 1,
) -> bool:
    """
    Send PDF to printer.
    color_mode: 'colour' or 'bw'
    Returns True on success.
    """
    printer = PRINTER_NAME or _get_default_printer()
    if not printer:
        logger.error("No printer found.")
        return False

    logger.info("Printing: '%s' | printer=%s | colour=%s | copies=%d",
                os.path.basename(pdf_path), printer, color_mode, copies)

    # ── SumatraPDF (best — supports colour settings) ──────────
    sumatra_paths = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            r"SumatraPDF\SumatraPDF.exe"
        ),
    ]
    sumatra = next((p for p in sumatra_paths if os.path.isfile(p)), None)

    if sumatra:
        # Build print settings string
        # colour → "color"  bw → "monochrome"
        colour_setting = "monochrome" if color_mode == "bw" else "color"
        settings = f"{colour_setting},noscale"

        cmd = [
            sumatra,
            "-print-to", printer,
            "-print-settings", settings,
            "-silent",
            pdf_path,
        ]

        # For multiple copies, send multiple times
        success = True
        for i in range(copies):
            try:
                result = subprocess.run(
                    cmd, timeout=120,
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.warning("SumatraPDF copy %d/%d exit=%d: %s",
                                   i+1, copies, result.returncode, result.stderr)
                    success = False
                else:
                    logger.info("SumatraPDF copy %d/%d sent ✅", i+1, copies)
            except subprocess.TimeoutExpired:
                logger.error("SumatraPDF timed out on copy %d", i+1)
                return False
            except Exception as exc:
                logger.error("SumatraPDF error copy %d: %s", i+1, exc)
                success = False

        if success:
            return True

    # ── Fallback: win32api ────────────────────────────────────
    try:
        import win32api
        for i in range(copies):
            win32api.ShellExecute(
                0, "printto", pdf_path, f'"{printer}"', ".", 0
            )
            logger.info("win32api copy %d/%d sent", i+1, copies)
        return True
    except Exception as exc:
        logger.error("win32api print failed: %s", exc)

    logger.error("All print methods failed for: %s", pdf_path)
    return False
