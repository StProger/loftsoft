from tortoise import fields
from tortoise.models import Model
from transliterate import translit


class Faq(Model):
    """пользовательское соглашение"""

    id = fields.BigIntField(pk=True)

    content = fields.TextField(null=False)
    title = fields.CharField(null=False, max_length=100, unique=True)

    order_id = fields.IntField(null=False)

    def slug(self) -> str:
        """
        slug для FAQ
        """
        return translit(
            self.title.replace(" ", "-").lower(), language_code="ru", reversed=True
        )

    class PydanticMeta:
        computed = ("slug",)

    class Meta:
        table = "faqs"
        ordering = ["order_id"]

    async def save(self, *args, **kwargs):
        """сохраняем и назначаем order_id"""
        last_faq_id = await Faq.all().order_by("id")

        if not last_faq_id:
            self.order_id = 1
        else:
            self.order_id = last_faq_id[-1].order_id + 1

        await super().save(*args, **kwargs)


async def change_faq_order(ids: list[int]) -> bool:
    """
    смена порядка в Faq
    """
    if not len(ids) == await Faq.all().count():
        return False

    faqs: list[Faq] = []

    # провера на существование категорий с таким ID
    for id_ in ids:
        faq_ = await Faq.get_or_none(id=id_)
        if not faq_:
            return False

        faqs.append(faq_)

    for faq_, order_id in zip(faqs, range(1, len(faqs) + 1)):
        faq_.order_id = order_id

    await Faq.bulk_update(faqs, fields=["order_id"])

    return True
