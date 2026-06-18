import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def log_time(label: str):
    start = time.perf_counter()
    yield
    duration = (time.perf_counter() - start) * 1000
    logger.info("Fetching %s took %.2f ms", label, duration)