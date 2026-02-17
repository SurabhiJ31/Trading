import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to INFO in production
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)