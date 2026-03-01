"""
=============================================================
  AutoPrint Pro — Smart Crop v2
  Stronger document detection for real-world photos.
  Handles: cards on bedsheets, tables, any background.
=============================================================
"""

import cv2
import numpy as np
from PIL import Image
from scripts.logger import logger


def _pil_to_cv2(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _cv2_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s    = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _perspective_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = _order_points(pts)
    tl, tr, br, bl = rect
    wA   = np.linalg.norm(br - bl)
    wB   = np.linalg.norm(tr - tl)
    maxW = max(int(wA), int(wB))
    hA   = np.linalg.norm(tr - br)
    hB   = np.linalg.norm(tl - bl)
    maxH = max(int(hA), int(hB))
    if maxW < 50 or maxH < 50:
        return image
    dst = np.array([
        [0, 0], [maxW-1, 0],
        [maxW-1, maxH-1], [0, maxH-1]
    ], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxW, maxH))


def _find_document_contour(edges: np.ndarray, min_area: float):
    """Try multiple contour finding strategies."""
    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Strategy 1: Look for exact 4-point polygon
    for cnt in contours[:15]:
        if cv2.contourArea(cnt) < min_area:
            continue
        peri   = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2)

    # Strategy 2: Relax to 4-6 points and take bounding box
    for cnt in contours[:10]:
        if cv2.contourArea(cnt) < min_area:
            continue
        peri   = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        if 3 <= len(approx) <= 6:
            x, y, w, h = cv2.boundingRect(approx)
            return np.array([
                [x, y], [x+w, y],
                [x+w, y+h], [x, y+h]
            ], dtype="float32")

    return None


def smart_crop_document(img: Image.Image) -> Image.Image:
    """
    Detect and crop document from any background.
    Tries multiple methods — falls back gracefully.
    """
    orig   = _pil_to_cv2(img)
    h, w   = orig.shape[:2]
    scale  = 1000 / max(h, w)
    small  = cv2.resize(orig, (int(w * scale), int(h * scale)))
    sh, sw = small.shape[:2]
    min_area = sw * sh * 0.08  # at least 8% of image

    doc_pts = None

    # ── Method 1: Canny on grayscale ─────────────────────────
    gray    = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    for lo, hi in [(20, 80), (10, 50), (30, 120)]:
        edges   = cv2.Canny(blurred, lo, hi)
        kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(edges, kernel, iterations=3)
        doc_pts = _find_document_contour(dilated, min_area)
        if doc_pts is not None:
            logger.info("Document found via Canny lo=%d hi=%d", lo, hi)
            break

    # ── Method 2: Threshold on grayscale ─────────────────────
    if doc_pts is None:
        logger.info("Trying threshold method")
        _, thresh = cv2.threshold(blurred, 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        closed  = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
        doc_pts = _find_document_contour(closed, min_area)
        if doc_pts is not None:
            logger.info("Document found via threshold")

    # ── Method 3: HSV colour difference ──────────────────────
    if doc_pts is None:
        logger.info("Trying HSV colour method")
        hsv     = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        s_chan   = hsv[:, :, 1]
        _, mask  = cv2.threshold(s_chan, 30, 255, cv2.THRESH_BINARY_INV)
        kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
        cleaned  = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=4)
        doc_pts  = _find_document_contour(cleaned, min_area)
        if doc_pts is not None:
            logger.info("Document found via HSV")

    # ── Method 4: White region detection ─────────────────────
    if doc_pts is None:
        logger.info("Trying white region detection")
        _, white = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed   = cv2.morphologyEx(white, cv2.MORPH_CLOSE, kernel, iterations=5)
        doc_pts  = _find_document_contour(closed, min_area)
        if doc_pts is not None:
            logger.info("Document found via white region")

    # ── Apply crop ────────────────────────────────────────────
    if doc_pts is not None:
        # Scale points back to original image size
        pts = doc_pts.astype("float32") / scale
        try:
            warped = _perspective_transform(orig, pts)
            result = _cv2_to_pil(warped)
            # Sanity check: result should be reasonable size
            if result.width > 100 and result.height > 100:
                logger.info(
                    "Smart crop: %dx%d → %dx%d",
                    w, h, result.width, result.height
                )
                return result
        except Exception as exc:
            logger.warning("Transform failed: %s", exc)

    # ── Final fallback: simple content crop ───────────────────
    logger.info("All smart crop methods failed — using simple content crop")
    return _simple_content_crop(img)


def _simple_content_crop(img: Image.Image) -> Image.Image:
    """Remove uniform borders."""
    gray = img.convert("L")
    arr  = np.array(gray)
    mask = arr < 240
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any() or not cols.any():
        return img
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    pad  = 10
    h, w = arr.shape
    return img.crop((
        max(0, cmin-pad), max(0, rmin-pad),
        min(w, cmax+pad), min(h, rmax+pad)
    ))
