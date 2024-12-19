from tortoise import fields
from tortoise.models import Model

from axegaoshop.services.cache.redis_service import rem_amount
from axegaoshop.services.utils import generate_unique_sum_postfix, random_upper_string


class Replenish(Model):
    """таблица с пополнениями баланса"""

    id = fields.IntField(pk=True)

    user = fields.ForeignKeyField("axegaoshop.User", related_name="replenishes")

    number = fields.CharField(
        max_length=50, unique=True, default=random_upper_string
    )  # номер платежа

    result_price = fields.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )  # окончательная цена с копейками

    payment_type = fields.CharField(
        max_length=100, null=False
    )  # выбранный способ оплаты  ("sbp")

    status = fields.CharField(
        max_length=100, default="waiting_payment"
    )  # статус пополнения (waiting_payment, canceled, finished)

    created_datetime = fields.DatetimeField(auto_now_add=True)  # дата создания платежа
    payed_datetime = fields.DatetimeField(auto_now=True)  # дата подтверждения оплаты

    class Meta:
        table = "replenishes"

    class PydanticMeta:
        exclude = ("user",)

    async def set_result_price(self, price: float):
        """установить итоговую цену исходя из всех товаров / количества одного товара"""
        price_postfix: float = await generate_unique_sum_postfix()

        self.result_price = float(price) + float(price_postfix)

        await self.save()

    async def cancel(self):
        """отменить заявку"""
        self.status = "canceled"
        await self.save()

    async def finish(self):
        """завершить заявку"""
        self.status = "finished"
        await rem_amount(float(self.result_price))
        await self.save()
