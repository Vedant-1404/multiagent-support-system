import os
import logging
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def get_checkpointer():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        from langgraph.checkpoint.redis import RedisSaver
        checkpointer = RedisSaver(redis_url)
        checkpointer.setup()
        logger.info(f"Redis checkpointer connected: {redis_url}")
        return checkpointer
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}), falling back to in-memory checkpointer")
        return MemorySaver()