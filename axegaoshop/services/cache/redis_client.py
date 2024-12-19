from redis.asyncio import Redis

from axegaoshop.settings import settings


def create_connection():
    """создание сесси Redis"""
    return Redis(
        host=settings.redis_host, port=settings.redis_port, decode_responses=True
    )


redis_pool = create_connection()
