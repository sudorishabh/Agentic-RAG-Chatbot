from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_redis() -> Any | None:
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        import redis
    except ImportError:
        logger.warning("redis_url is set but the 'redis' package is not installed.")
        return None
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
