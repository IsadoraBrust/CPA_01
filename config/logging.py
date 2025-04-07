import logging
import os

LOG_FORMAT_FILE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_TERMINAL = "%(levelname)s - %(message)s"
LOG_PATH = "logs"
LOG_FILE = "main.log"


def create_log_directory():
    """Create the log directory if it doesn't exist."""
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

def setup_file_handler():
    """Set up and return a file handler with the specified format."""
    file_handler = logging.FileHandler(os.path.join(LOG_PATH, LOG_FILE), encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT_FILE)
    file_handler.setFormatter(file_formatter)
    return file_handler

def setup_stream_handler():
    """Set up and return a stream handler with the specified format."""
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter(LOG_FORMAT_TERMINAL)
    stream_handler.setFormatter(stream_formatter)
    return stream_handler


def setup_logging():
    """Set up logging configuration."""
    if len(logging.getLogger().handlers):
        return
    
    create_log_directory()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Add handlers
    logger.addHandler(setup_file_handler())
    logger.addHandler(setup_stream_handler())

    logging.info("Logging configured.")