from axegaoshop.services.cache.redis_client import redis_pool
from axegaoshop.settings import settings


async def add_amount(amount: float) -> None:
    """добавление значения копеек которые в использование в кеш"""
    await redis_pool.sadd(settings.redis_amounts_key, amount)


async def rem_amount(amount: float) -> None:
    """удаление значения копеек из кеша"""
    if not amount:
        return
    await redis_pool.srem(settings.redis_amounts_key, amount)


async def amount_exists(amount: float) -> bool:
    """есть ли в кеше это значение или нет"""
    return await redis_pool.sismember(settings.redis_amounts_key, amount)
