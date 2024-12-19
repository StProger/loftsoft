from datetime import datetime

from tortoise import fields
from tortoise.exceptions import NoValuesFetched
from tortoise.models import Model
from transliterate import translit


class Subcategory(Model):
    """таблица с подкатегориями
    (Операционные системы -> *Windows*, *Linux*...)"""

    id = fields.IntField(pk=True)

    created_datetime = fields.DatetimeField(default=datetime.now)

    title = fields.CharField(max_length=500)

    category: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "axegaoshop.Category", related_name="subcategories"
    )

    order_id = fields.IntField(null=False)

    products: fields.ReverseRelation

    class Meta:
        table = "subcategories"
        ordering = ["order_id"]

    def product_count(self) -> int:
        """получение количество товаров в подкатегории"""
        try:
            return len(self.products)
        except (NoValuesFetched, AttributeError):
            return 0

    def slug(self) -> str:
        """
        slug для подкатегории
        """
        return (
            translit(
                self.title.replace(" ", "-").lower(), language_code="ru", reversed=True
            )
            + "-"
            + str(self.id)
        )

    class PydanticMeta:
        computed = ("product_count", "slug")
        allow_cycles = True
        max_recursion = 3

    async def save(self, *args, **kwargs):
        """сохраняем и назначаем order_id"""
        if not kwargs.get("repeat"):
            last_cat_id = await Subcategory.filter(
                category_id=self.category_id
            ).order_by("id")
            if not last_cat_id:
                self.order_id = 1
            else:
                self.order_id = last_cat_id[-1].id + 1
        else:
            del kwargs["repeat"]
        await super().save(*args, **kwargs)


async def change_subcategory_order(ids: list[int]) -> bool:
    """
    смена порядка в подкатегориях

    Алгоритм:
        На вход принимается список ID подкатегорий в измененном порядке,
        затем по порядку этих ID изменяется поле order_id в бд

    :param ids: список айдишников подкатегорий из бд
    :return: True - успех / False - ошибка

    """
    if not len(ids) == await Subcategory.all().count():
        return False

    subcategories: list[Subcategory] = []

    # провера на существование категорий с таким ID
    for id_ in ids:
        subcat = await Subcategory.get_or_none(id=id_)
        if not subcat:
            return False

        subcategories.append(subcat)

    for cat, order_id in zip(subcategories, range(1, len(subcategories) + 1)):
        cat.order_id = order_id

    await Subcategory.bulk_update(subcategories, fields=["order_id"])

    return True
