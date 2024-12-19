from axegaoshop.db.models.telegram_settings import get_tg_recievers, get_tg_settings

from .service import TelegramService


async def get_telegram_data():
    """получение данных по телеграмму для уведов"""
    telegram_settings = await get_tg_settings()

    error = False
    if not telegram_settings:
        error = True

    recievers = await get_tg_recievers()

    if not recievers:
        error = True

    if error:
        return None

    if not error:
        a = TelegramService(telegram_settings.token, [r.telegram_id for r in recievers])
        return a

    return None


async def check_valid(token: str):
    """проверка на валидность введенного в админке токена"""
    tg_ = TelegramService(token, [])

    if not tg_.available():
        return False
    return True
