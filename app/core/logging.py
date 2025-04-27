import logging
import sys
import os
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


def setup_logging(
    log_level: str = None, 
    log_file: Optional[str] = None,
    app_name: str = None
) -> logging.Logger:
    """Configure and return a logger.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to a log file
        app_name: Name of the application for logger identification
    
    Returns:
        Configured logger instance
    """
    # Get settings values if not provided
    if log_level is None:
        log_level = "DEBUG" if settings.DEBUG else "INFO"
    
    if app_name is None:
        app_name = settings.APP_NAME
    
    # Set up numeric logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging_config = {
        "level": numeric_level,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }
    
    # Always create a logs directory
    logs_dir = "logs"
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    # Default log file location if not specified
    if log_file is None:
        log_file = os.path.join(logs_dir, "app.log")
        
    logging_config["filename"] = log_file
    logging_config["filemode"] = "a"  # Append mode
    
    # Apply configuration
    logging.basicConfig(**logging_config)
    
    # Create and return logger
    logger = logging.getLogger(app_name)
    logger.setLevel(numeric_level)
    
    # Add stream handler to output to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    formatter = logging.Formatter(logging_config["format"], logging_config["datefmt"])
    console_handler.setFormatter(formatter)
    
    # Only add the handler if it's not already there
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        logger.addHandler(console_handler)
    
    return logger


# Create default application logger
app_logger = setup_logging(log_file="logs/app.log") 