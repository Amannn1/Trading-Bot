"""
Logging configuration for the trading bot.
Sets up both file and console logging with structured format.
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "trading_bot") -> logging.Logger:
    """
    Set up and return a logger that writes to both a log file and the console.

    Args:
        name: Logger name (used to identify source in log entries)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Ensure logs directory exists
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Log file named with today's date for easy reference
    log_filename = os.path.join(logs_dir, f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log")

    # --- File Handler: DEBUG and above, full detail ---
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)

    # --- Console Handler: INFO and above, clean output ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        fmt="%(levelname)-8s | %(message)s"
    )
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialised — writing to: {log_filename}")
    return logger
