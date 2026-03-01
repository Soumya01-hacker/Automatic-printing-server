"""
=============================================================
  AutoPrint Server - Logger
=============================================================
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from config.config import LOG_DIR, LOG_LEVEL, LOG_ROTATION, LOG_BACKUP_COUNT


def setup_logger(name: str = "autoprint") -> logging.Logger:
    """Configure and return the application logger."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "autoprint.log")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if logger.handlers:
        return logger  # Already configured

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler – rotates daily
    file_handler = TimedRotatingFileHandler(
        log_file,
        when=LOG_ROTATION,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Singleton logger instance
logger = setup_logger()
