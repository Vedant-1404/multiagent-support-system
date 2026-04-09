import os
import logging
from langgraph.checkpoint.redis import RedisSaver

logger = logging.getLogger(__name__)


def get_checkpointer():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        checkpointer = RedisSaver.from_conn_string(redis_url)
        logger.info(f"Redis checkpointer connected: {redis_url}")
        return checkpointer
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}), falling back to in-memory checkpointer")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
