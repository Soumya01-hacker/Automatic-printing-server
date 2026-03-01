"""
=============================================================
  AutoPrint Pro — Smart Document Processor
  - OpenCV smart crop (detects doc on any background)
  - Colour printing fixed
  - Enhancement only when truly needed
  - LIC = direct print, zero processing
=============================================================
"""

import os
import tempfile
from pathlib import Path
from typing import Tuple

import fitz
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import A3, A4, A5, B5, landscape, portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from config.config import (
    OCR_LANGUAGE,
    PROCESSED_DIR,
    TESSERACT_CMD,
)
from scripts.command_parser import PrintCommand
from scripts.document_detector import DocumentInfo
from scripts.logger import logger
from scripts.smart_crop import smart_crop_document, _simple_content_crop

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

PAGE_SIZES = {
    "A4":     A4,
    "A3":     A3,
    "A5":     A5,
    "B5":     B5,
    "LETTER": (612, 792),
    "LEGAL":  (612, 1008),
}


def _get_page_size(cmd: PrintCommand) -> Tuple[float, float]:
    base = PAGE_SIZES.get(cmd.page_size.upper(), A4)
    if cmd.orientation == "landscape":
        return landscape(base)
    return portrait(base)


# ── Quality Checks ───────────────────────────────────────────

def _check_orientation(img: Image.Image) -> int:
    """Returns rotation angle needed. 0 if check fails."""
    try:
        osd   = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
        angle = int(osd.get("rotate", 0))
        return angle if angle in (90, 180, 270) else 0
    except Exception:
        return 0


def _check_needs_enhancement(img: Image.Image) -> bool:
    """Only enhance truly faded/dark images."""
    gray = img.convert("L")
    arr  = np.array(gray, dtype=np.float32)
    std  = arr.std()
    mean = arr.mean()
    needs = std < 25 or mean < 40
    logger.debug("Enhancement: std=%.1f mean=%.1f needed=%s", std, mean, needs)
    return needs


def _has_background(img: Image.Image) -> bool:
    """
    Returns True if image has messy background (bedsheet, table etc.)
    Returns False if already clean — skips smart crop for clean images.
    """
    arr  = np.array(img.convert("RGB"))
    h, w = arr.shape[:2]
    m    = int(min(h, w) * 0.05)
    corners = [
        arr[:m, :m], arr[:m, w-m:],
        arr[h-m:, :m], arr[h-m:, w-m:],
    ]
    if all(patch.mean() > 220 for patch in corners):
        return False
    avg_var = sum(p.std() for p in corners) / 4
    has_bg  = avg_var > 30
    logger.debug("Background check: variance=%.1f has_bg=%s", avg_var, has_bg)
    return has_bg


# ── Processing Operations ─────────────────────────────────────

def _fix_orientation(img: Image.Image, angle: int) -> Image.Image:
    logger.info("Rotating %d degrees", angle)
    return img.rotate(angle, expand=True, fillcolor=255)


def _gentle_enhance(img: Image.Image) -> Image.Image:
    logger.info("Gentle enhancement applied")
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Sharpness(img).enhance(1.2)
    return img


# ── PDF Builders ─────────────────────────────────────────────

def _render_image_to_pdf(
    img: Image.Image, output_path: str, cmd: PrintCommand
) -> None:
    pw, ph = _get_page_size(cmd)
    if cmd.color_mode == "bw":
        img = img.convert("L").convert("RGB")
    else:
        img = img.convert("RGB")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    img.save(tmp_path, "PNG", dpi=(300, 300))

    iw, ih = img.size
    margin = 20
    scale  = min((pw - 2 * margin) / iw, (ph - 2 * margin) / ih)
    dw, dh = iw * scale, ih * scale
    x      = (pw - dw) / 2
    y      = (ph - dh) / 2

    c = canvas.Canvas(output_path, pagesize=(pw, ph))
    c.drawImage(ImageReader(tmp_path), x, y, width=dw, height=dh,
                preserveAspectRatio=True)
    c.showPage()
    c.save()
    os.unlink(tmp_path)


def _render_pdf_to_print_pdf(
    input_path: str, output_path: str, cmd: PrintCommand
) -> int:
    pw, ph     = _get_page_size(cmd)
    page_count = 0

    with fitz.open(input_path) as doc:
        c = canvas.Canvas(output_path, pagesize=(pw, ph))
        for page in doc:
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            pix.save(tmp_path)

            with Image.open(tmp_path) as img:
                if cmd.color_mode == "bw":
                    img = img.convert("L").convert("RGB")
                    img.save(tmp_path, "PNG")
                iw, ih = img.size

            margin = 20
            scale  = min((pw - 2 * margin) / iw, (ph - 2 * margin) / ih)
            dw, dh = iw * scale, ih * scale
            x      = (pw - dw) / 2
            y      = (ph - dh) / 2

            c.drawImage(ImageReader(tmp_path), x, y, width=dw, height=dh,
                        preserveAspectRatio=True)
            c.showPage()
            os.unlink(tmp_path)
            page_count += 1
        c.save()
    return page_count


# ── Main Pipeline ─────────────────────────────────────────────

def process_document(
    file_path: str,
    doc_info: DocumentInfo,
) -> Tuple[str, int]:
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    stem       = Path(file_path).stem
    output_pdf = os.path.join(PROCESSED_DIR, f"{stem}_print.pdf")
    ext        = Path(file_path).suffix.lower()
    cmd        = doc_info.print_cmd

    # ══════════════════════════════════════════════════════
    #  LIC RECEIPT — REFORMAT ONLY, NO PROCESSING
    # ══════════════════════════════════════════════════════
    if doc_info.is_lic:
        logger.info("LIC Receipt — direct reformat only")
        if ext == ".pdf":
            pages = _render_pdf_to_print_pdf(file_path, output_pdf, cmd)
            return output_pdf, pages
        else:
            with Image.open(file_path) as img:
                _render_image_to_pdf(img.copy(), output_pdf, cmd)
            return output_pdf, 1

    # ══════════════════════════════════════════════════════
    #  IMAGE FILES — SMART CROP + ORIENTATION + ENHANCE
    # ══════════════════════════════════════════════════════
    if ext in {".jpg", ".jpeg", ".png"}:
        with Image.open(file_path) as raw:
            img = raw.copy().convert("RGB")

        # Step 1: Fix orientation first
        angle = _check_orientation(img)
        if angle:
            img = _fix_orientation(img, angle)

        # Step 2: Smart crop — only if background detected
        if _has_background(img):
            logger.info("Background detected — running smart crop")
            img = smart_crop_document(img)
        else:
            logger.info("Clean image — skipping smart crop")

        # Step 3: Enhance only if needed
        if _check_needs_enhancement(img):
            img = _gentle_enhance(img)

        _render_image_to_pdf(img, output_pdf, cmd)
        return output_pdf, 1

    # ══════════════════════════════════════════════════════
    #  PDF FILES — SMART PROCESSING
    # ══════════════════════════════════════════════════════
    if ext == ".pdf":
        # Sample first page for checks
        with fitz.open(file_path) as doc:
            pix        = doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            sample_img = Image.frombytes(
                "RGB", (pix.width, pix.height), pix.samples
            )

        angle  = _check_orientation(sample_img)
        do_enh = _check_needs_enhancement(sample_img)

        logger.info("PDF checks → rotate=%d enhance=%s", angle, do_enh)

        # If nothing needs fixing — just reformat
        if not angle and not do_enh:
            logger.info("PDF looks good — just reformatting")
            pages = _render_pdf_to_print_pdf(file_path, output_pdf, cmd)
            return output_pdf, pages

        # Process page by page
        with fitz.open(file_path) as doc:
            c          = canvas.Canvas(output_pdf, pagesize=_get_page_size(cmd))
            pw, ph     = _get_page_size(cmd)
            page_count = 0

            for page in doc:
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                if angle:
                    img = _fix_orientation(img, angle)
                if do_enh:
                    img = _gentle_enhance(img)
                if cmd.color_mode == "bw":
                    img = img.convert("L").convert("RGB")

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                img.save(tmp_path, "PNG")

                iw, ih = img.size
                margin = 20
                scale  = min((pw - 2 * margin) / iw, (ph - 2 * margin) / ih)
                dw, dh = iw * scale, ih * scale
                x      = (pw - dw) / 2
                y      = (ph - dh) / 2

                c.drawImage(ImageReader(tmp_path), x, y, width=dw, height=dh,
                            preserveAspectRatio=True)
                c.showPage()
                os.unlink(tmp_path)
                page_count += 1

            c.save()
        return output_pdf, page_count

    raise ValueError(f"Unsupported file: {ext}")
