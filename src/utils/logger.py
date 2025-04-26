import logging
import sys

def setup_logging(level=logging.INFO):
    """Set up logging for the application."""
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    
    # Create a logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging configured")
    
    return logger 