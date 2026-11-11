import logging

from ..persistence.repositories.health import database_available

logger = logging.getLogger(__name__)


def check_readiness():
    if not database_available():
        logger.warning("Readiness check: database unavailable")
        return {"status": "degraded", "checks": {"db": "err"}}
    return {"status": "ok", "checks": {"db": "ok"}}
