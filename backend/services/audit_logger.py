import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("audit")


def log_event(event_type: str, user: str, details: dict):
    """Write a structured audit log entry."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "user": user,
        "details": details,
    }
    logger.info("AUDIT | %s", entry)
    return entry
