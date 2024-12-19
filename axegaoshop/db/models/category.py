import transliterate
from tortoise import fields
from tortoise.exceptions import NoValuesFetched
from tortoise.fields import JSONField
from tortoise.models import Model
from transliterate import translit


class Category(Model):
    """таблица с категориями
    (Операционные системы, Офис, Безопасность...)"""

    id = fields.IntField(pk=True)

    created_datetime = fields.DatetimeField(auto_now_add=True)

    title = fields.CharField(max_length=500)
    photo = fields.CharField(max_length=200, null=True)
    colors = JSONField(default=[])  # цвета в HEX

    order_id = fields.IntField(null=False)

    subcategories: fields.ReverseRelation

    class Meta:
        table = "categories"
        ordering = ["order_id"]

    def subcategories_count(self) -> int:
        """
        посчитанное количество подкатегорий в категории
        """
        try:
            return len(self.subcategories)
        except NoValuesFetched:
            return 0

    def slug(self) -> str:
        """
        slug для категории
        """
        return (
            translit(
                self.title.replace(" ", "-").lower(), language_code="ru", reversed=True
            )
            + "-"
            + str(self.id)
        )

    class PydanticMeta:
        computed = ("subcategories_count", "slug")
        exclude = ("subcategories.products.shop_cart",)
        max_recursion = 3

    async def save(self, *args, **kwargs):
        """сохраняем и назначаем order_id"""
        last_cat_id = await Category.all().order_by("id")

        if not last_cat_id:
            self.order_id = 1
        else:
            self.order_id = last_cat_id[-1].order_id + 1

        await super().save(*args, **kwargs)


async def change_category_order(ids: list[int]) -> bool:
    """
    смена порядка в категориях

    Алгоритм:
        На вход принимается список ID категорий в измененном порядке,
        затем по порядку этих ID изменяется поле order_id в бд

    :param ids: список айдишников категорий из бд
    :return: True - успеш / False - ошибка

    """
    if not len(ids) == await Category.all().count():
        return False

    categories: list[Category] = []

    # провера на существование категорий с таким ID
    for id_ in ids:
        cat = await Category.get_or_none(id=id_)
        if not cat:
            return False

        categories.append(cat)

    for cat, order_id in zip(categories, range(1, len(categories) + 1)):
        cat.order_id = order_id

    await Category.bulk_update(categories, fields=["order_id"])

    return True
