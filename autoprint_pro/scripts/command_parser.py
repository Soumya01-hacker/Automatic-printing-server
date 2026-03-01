"""
=============================================================
  AutoPrint Pro — Smart Command Parser
  Reads email body text and extracts print instructions.
  Supports English + Hindi commands.
=============================================================
"""

import re
from dataclasses import dataclass
from typing import Optional

from config.config import (
    DEFAULT_COLOR_MODE,
    DEFAULT_COPIES,
    DEFAULT_ORIENTATION,
    DEFAULT_PAGE_SIZE,
)


@dataclass
class PrintCommand:
    """Holds all print settings extracted from email body."""
    page_size:   str  = DEFAULT_PAGE_SIZE    # A4, A3, B5
    color_mode:  str  = DEFAULT_COLOR_MODE   # colour, bw
    copies:      int  = DEFAULT_COPIES       # 1, 2, 3...
    orientation: str  = DEFAULT_ORIENTATION  # portrait, landscape
    has_command: bool = False                # True if any command found


# ── Keyword Maps ─────────────────────────────────────────────

SIZE_KEYWORDS = {
    "a4":        "A4",
    "a 4":       "A4",
    "a3":        "A3",
    "a 3":       "A3",
    "b5":        "B5",
    "b 5":       "B5",
    "a5":        "A5",
    "a 5":       "A5",
    "letter":    "LETTER",
    "legal":     "LEGAL",
}

COLOR_KEYWORDS_COLOUR = [
    "colour", "color", "coloured", "colored",
    "in colour", "in color",
    "rang mein", "colour mein", "color mein",
    "colour print", "color print",
    "colur",   # common typo
]

COLOR_KEYWORDS_BW = [
    "black", "black and white", "black & white",
    "b&w", "bw", "b/w",
    "black white", "grayscale", "greyscale",
    "kala safed", "black mein", "black me",
    "without colour", "without color",
    "no colour", "no color",
    "black print",
]

ORIENTATION_LANDSCAPE = [
    "landscape", "horizontal",
    "wide", "sideways",
]

ORIENTATION_PORTRAIT = [
    "portrait", "vertical", "upright",
]


def _extract_copies(text: str) -> Optional[int]:
    """
    Extract number of copies from text.
    Handles: '2 copies', '3 copy', 'two copies',
             '2 copy chahiye', 'teen copies'
    """
    # Word numbers (Hindi + English)
    word_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
    }

    # Pattern: "2 copies" or "2 copy"
    match = re.search(r"(\d+)\s*cop(?:y|ies)", text, re.IGNORECASE)
    if match:
        n = int(match.group(1))
        if 1 <= n <= 25:
            return n

    # Pattern: "two copies" or "do copy"
    for word, num in word_map.items():
        pattern = rf"\b{word}\s+cop(?:y|ies)\b"
        if re.search(pattern, text, re.IGNORECASE):
            return num

    # Pattern: "print 3" or "3 print"
    match = re.search(r"(?:print\s+(\d+)|(\d+)\s+print)", text, re.IGNORECASE)
    if match:
        n = int(match.group(1) or match.group(2))
        if 1 <= n <= 25:
            return n

    return None


def parse_email_commands(email_body: str) -> PrintCommand:
    """
    Parse the email body and return a PrintCommand with all settings.
    If no commands found, returns defaults with has_command=False.
    """
    if not email_body:
        return PrintCommand()

    text = email_body.lower().strip()
    cmd  = PrintCommand()

    # ── Page Size ─────────────────────────────────────────────
    for keyword, size in SIZE_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            cmd.page_size   = size
            cmd.has_command = True
            break

    # ── Colour Mode ───────────────────────────────────────────
    # Check BW first (more specific)
    for kw in COLOR_KEYWORDS_BW:
        if kw in text:
            cmd.color_mode  = "bw"
            cmd.has_command = True
            break
    else:
        for kw in COLOR_KEYWORDS_COLOUR:
            if kw in text:
                cmd.color_mode  = "colour"
                cmd.has_command = True
                break

    # ── Orientation ───────────────────────────────────────────
    for kw in ORIENTATION_LANDSCAPE:
        if kw in text:
            cmd.orientation = "landscape"
            cmd.has_command = True
            break
    for kw in ORIENTATION_PORTRAIT:
        if kw in text:
            cmd.orientation = "portrait"
            cmd.has_command = True
            break

    # ── Copies ────────────────────────────────────────────────
    copies = _extract_copies(text)
    if copies:
        cmd.copies      = copies
        cmd.has_command = True

    return cmd
