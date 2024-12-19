from tortoise import fields
from tortoise.models import Model


class Review(Model):
    """таблица с отзывами на Product"""

    id = fields.IntField(pk=True)

    status = fields.TextField(
        null=False, default="wait_for_accept"
    )  # статусы: (wait_for_accept, accepted, declined)

    text = fields.TextField(null=False)  # текст отзыва

    rate = fields.IntField(null=False)  # максимум 5 звезд

    created_datetime = fields.DatetimeField(null=False, auto_now_add=True)
    approved_datetime = fields.DatetimeField(null=False, auto_now=True)

    order = fields.ForeignKeyField(
        "axegaoshop.Order", related_name="reviews", unique=False
    )
    product = fields.ForeignKeyField(
        "axegaoshop.Product", related_name="reviews", unique=False
    )

    user = fields.ForeignKeyField("axegaoshop.User", related_name="reviews")

    photos: fields.ForeignKeyNullableRelation["ReviewPhoto"]

    class Meta:
        table = "reviews"
        ordering = ["-approved_datetime"]

    async def set_status(self, status: str):
        """установка статуса отзыву"""
        self.status = status
        await self.save()


class ReviewPhoto(Model):
    id = fields.IntField(pk=True)

    photo = fields.TextField(null=False)
    review = fields.ForeignKeyField("axegaoshop.Review", related_name="review_photos")

    class Meta:
        table = "review_photos"
