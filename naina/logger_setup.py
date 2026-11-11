# naina/logger_setup.py
import sys
from loguru import logger
from naina.config import LOG_FILE, LOG_LEVEL

def setup_logger():
    logger.remove()
    logger.add(sys.stderr, level=LOG_LEVEL,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> — <level>{message}</level>")
    logger.add(str(LOG_FILE), level="DEBUG", rotation="10 MB", retention="7 days",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}")
    return logger
