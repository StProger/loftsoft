from tortoise import fields
from tortoise.expressions import F
from tortoise.fields import ReverseRelation
from tortoise.models import Model


class Promocode(Model):
    """таблица с промокодами"""

    id = fields.IntField(pk=True)

    name = fields.CharField(max_length=100, unique=True)
    activations_count = fields.IntField(default=1)
    sale_percent = fields.FloatField()

    created_datetime = fields.DatetimeField(auto_now_add=True)

    orders: ReverseRelation

    class Meta:
        table = "promocodes"

    class PydanticMeta:
        exclude = ("created_datetime", "orders")

    async def use(self):
        """используем промокод"""
        if not self.activations_count == -1:
            await Promocode.filter(id=self.id).update(
                activations_count=F("activations_count") - 1
            )

    async def active(self):
        """проверка на активность промокода"""
        return self.activations_count == -1 or self.activations_count > 0
