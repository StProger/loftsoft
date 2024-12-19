import random
import string

from axegaoshop.services.cache.redis_service import add_amount, amount_exists


def random_string(length: int = 16) -> str:  # noqa
    return "".join(
        [random.choice(string.ascii_letters + string.digits) for _ in range(length)]
    )


def random_upper_string():  # noqa
    return random_string(8).upper()


async def generate_unique_sum_postfix():
    """генерация уникального значения копеек"""
    value = random.uniform(0, 0.99)
    f_value = float("{0:.2f}".format(value))
    if not await amount_exists(f_value):
        await add_amount(f_value)
        return "{0:.2f}".format(value)
    else:
        return await generate_unique_sum_postfix()
