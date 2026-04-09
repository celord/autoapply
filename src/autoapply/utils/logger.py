"""
Logger configuration utility for AutoJobFinder
"""

import sys
from pathlib import Path
from loguru import logger

def setup_logger(log_path: Path, level: str = "INFO", rotation: str = "10 MB", retention: int = 5):
    """
    Configure the logger with the specified settings.
    
    Args:
        log_path (Path): Path to the log file
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation (str): When to rotate the log file (e.g., "10 MB", "1 day")
        retention (int): Number of log files to retain
    """
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # Add file logger
    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation=rotation,
        retention=retention,
        compression="zip"
    )
    
    logger.info(f"Logger initialized - Log file: {log_path}")
    return logger 