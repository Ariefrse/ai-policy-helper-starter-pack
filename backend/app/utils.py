import time
import logging

# Configure structured logging
logger = logging.getLogger(__name__)

def retry_with_backoff(func, max_retries=3, base_delay=1.0, max_delay=30.0, operation_name="operation"):
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        operation_name: Name of the operation for logging

    Returns:
        Result of the function execution or None if all retries fail
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Failed {operation_name} after {max_retries + 1} attempts: {str(e)}")
                return None

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"{operation_name} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying in {delay:.2f}s...")
            time.sleep(delay)

    return None