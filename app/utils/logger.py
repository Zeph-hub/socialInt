import os
import sys
from loguru import logger
from app.core.config import settings

def setup_logger():
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        enqueue=True,
    )
    
    # Add file handler for JSON structured logs
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger.add(
        os.path.join(log_dir, "pipeline_{time}.json"),
        format="{message}",
        level="DEBUG",
        serialize=True,
        rotation="1 day",
        retention="7 days",
        enqueue=True,
    )
    
    return logger

log = setup_logger()
