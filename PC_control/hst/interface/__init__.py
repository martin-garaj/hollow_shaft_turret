import logging
from ..config import LOGGER_LEVEL
from .interface import Interface

# Initialize logger with class name
logger = logging.getLogger(__name__)
# Create console handler and set level to INFO
console_handler = logging.StreamHandler()
# Create formatter
formatter = logging.Formatter('{asctime} - {name:<34s} - {levelname:<8s} - {message}', style='{')
# Add formatter to console handler
console_handler.setFormatter(formatter)
# Add console handler to logger
logger.addHandler(console_handler)
# Set debugging level
logger.setLevel(LOGGER_LEVEL)