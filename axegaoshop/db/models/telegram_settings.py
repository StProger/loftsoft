from tortoise import fields
from tortoise.models import Model


class TelegramSetting(Model):
    """таблица с данными об уведомлениях в телеграмм"""

    id = fields.IntField(pk=True)

    token = fields.TextField(null=False)  # токен бота

    class Meta:
        table = "telegram_settings"


class TelegramReciever(Model):
    """таблица с получателями уведов в телеграммк"""

    id = fields.IntField(pk=True)

    telegram_id = fields.BigIntField(null=False)  # ID в телеграмме

    class Meta:
        table = "telegram_recievers"


async def get_tg_settings() -> TelegramSetting | None:
    """получение настроек отправки в телеграмм

    если настройки не заданы - возвращается None"""
    tg_data = TelegramSetting.all()

    if not await tg_data.exists():
        return None

    return await tg_data.first()


async def get_tg_recievers() -> list[TelegramReciever] | None:
    """получение получателей

    если нет ни одного - возаращается None"""
    recievers = TelegramReciever.all()

    if not await recievers.exists():
        return []

    return await recievers.all()
