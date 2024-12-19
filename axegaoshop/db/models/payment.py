from tortoise import fields
from tortoise.models import Model


class Payment(Model):
    """таблица с данными об оплате"""

    id = fields.IntField(pk=True)
