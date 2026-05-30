import json
import logging
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "sandbox" / "logs"
LOG_FILE = LOG_DIR / "audit.log"
AUDIT_LOGGER_NAME = "oblak.audit"


def configure_audit_logger():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return

    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def audit(event: str, **fields):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    logging.getLogger(AUDIT_LOGGER_NAME).info(
        json.dumps(record, ensure_ascii=False, sort_keys=True)
    )
