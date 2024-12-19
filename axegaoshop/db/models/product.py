from datetime import datetime

from tortoise import fields
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet
from transliterate import translit


class Product(Model):
    """таблица с товарами (винда 11, винда 10...)"""

    id = fields.IntField(pk=True)

    created_datetime = fields.DatetimeField(default=datetime.now)

    title = fields.CharField(max_length=500, null=False)
    description = fields.TextField()

    card_price = fields.DecimalField(
        max_digits=10, decimal_places=2
    )  # цена на карточке из первой версии товара
    card_has_sale = fields.BooleanField(default=False)  # скидка из первой версии товара
    card_sale_price = fields.DecimalField(
        max_digits=10, decimal_places=2
    )  # скидка из первой версии товара

    subcategory: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "axegaoshop.Subcategory", related_name="products"
    )
    order_id = fields.BigIntField(null=False)

    parameters: fields.ReverseRelation["Parameter"]
    photos: fields.ReverseRelation["ProductPhoto"]
    options: fields.ReverseRelation["Option"]
    shop_cart: fields.ReverseRelation

    def sale_percent(self) -> int:
        """процент скидки (высчитывается автоматом в пидантик модель)"""

        return 100 - int((self.card_sale_price * 100) / self.card_price)

    def slug(self) -> str:
        """
        slug для товара
        """
        return (
            translit(
                self.title.replace(" ", "-").lower(), language_code="ru", reversed=True
            )
            + "-"
            + str(self.id)
        )

    class Meta:
        table = "products"
        ordering = ["order_id"]

    class PydanticMeta:
        exclude = ("subcategory", "shop_cart", "created_datetime", "reviews")
        computed = ("sale_percent", "slug")

    async def save(self, *args, **kwargs):
        """сохраняем и назначаем order_id"""

        if not kwargs.get("repeat"):
            last_product_id = await Product.filter(
                subcategory_id=self.subcategory_id
            ).order_by("id")

            if not last_product_id:
                self.order_id = 1
            else:
                self.order_id = last_product_id[-1].order_id + 1
        else:
            del kwargs["repeat"]
        await super().save(*args, **kwargs)


class Parameter(Model):
    """таблица с параметрами - версиями товара (винда домашняя, винда профессиональная...)"""

    id = fields.IntField(pk=True)

    title = fields.TextField(null=False)
    description = fields.TextField(null=True)

    price = fields.DecimalField(max_digits=10, decimal_places=2, null=False)

    has_sale = fields.BooleanField(default=False)
    sale_price = fields.DecimalField(max_digits=10, decimal_places=2)

    give_type = fields.CharField(
        max_length=30, null=False, default="string"
    )  # string/file/hand - тип выдачи товара

    product: fields.ForeignKeyRelation[Product] = fields.ForeignKeyField(
        "axegaoshop.Product", related_name="parameters"
    )

    order_id = fields.IntField(null=False)

    shop_cart: fields.ReverseRelation
    data: fields.ReverseRelation["ProductData"]
    order_parameters: fields.ReverseRelation

    def sale_percent(self) -> int | None:
        """процент скидки (высчитывается автоматом в пидантик модель)"""

        return (
            100 - int((self.sale_price * 100) / self.price) if self.has_sale else None
        )

    class Meta:
        table = "parameters"
        ordering = ["order_id"]

    class PydanticMeta:
        exclude = ["shop_cart", "product", "data", "order_parameters", "reviews"]
        computed = ("sale_percent",)

    async def save(self, *args, **kwargs):
        """сохраняем и назначаем order_id"""
        if not kwargs.get("repeat"):
            last_param_id = await Parameter.filter(product_id=self.product_id).order_by(
                "id"
            )

            if not last_param_id:
                self.order_id = 1
            else:
                self.order_id = last_param_id[-1].order_id + 1
        else:
            del kwargs["repeat"]
        await super().save(*args, **kwargs)

    async def get_price(self):
        """get result price for one parameter"""
        if self.has_sale:
            return self.sale_price
        else:
            return self.price


class ProductData(Model):
    """таблица с самими товарами (ключами..)"""

    id = fields.IntField(pk=True)

    parameter: fields.ForeignKeyRelation["Parameter"] = fields.ForeignKeyField(
        "axegaoshop.Parameter", related_name="data"
    )

    value = fields.TextField(null=False)

    is_active = fields.BooleanField(default=True, null=False)

    order: fields.ForeignKeyNullableRelation = fields.ForeignKeyField(
        "axegaoshop.Order", related_name="data", null=True
    )

    class PydanticMeta:
        exclude = ("parameer", "is_active")

    class Meta:
        table = "product_data"


class Option(Model):
    """таблица с характеристиками (код, метод установки...)"""

    id = fields.IntField(pk=True)

    title = fields.TextField(null=False)

    value = fields.TextField(null=False)

    is_pk = fields.BooleanField(default=False)

    product: fields.ForeignKeyRelation[Product] = fields.ForeignKeyField(
        "axegaoshop.Product", related_name="options"
    )

    class Meta:
        table = "options"

    class PydanticMeta:
        exclude = ("product",)

    async def save(self, *args, **kwargs):
        """сохраняем, но перед этим
        проверяем, если такой параметр же где то стоит (код товара),
        возвращаем ошибку"""
        # if self.is_pk:
        #     if await Option.get_or_none(value=self.value):
        #         return "ALREADY_HAVE"

        await super().save(*args, **kwargs)

    async def is_available(self) -> bool:
        if self.is_pk:
            query = await Option.filter(Q(title=self.title) & Q(value=self.value))

            if query:
                return False
        return True


class ProductPhoto(Model):
    """фотографии к товарам"""

    id = fields.IntField(pk=True)

    photo = fields.CharField(max_length=200)

    main = fields.BooleanField(default=False)

    product: fields.ForeignKeyRelation[Product] = fields.ForeignKeyField(
        "axegaoshop.Product", related_name="product_photos"
    )

    class Meta:
        table = "product_photos"
        ordering = ["-main"]

    class PydanticMeta:
        exclude = ("product",)


async def change_product_order(ids: list[int]) -> bool:
    """
    смена порядка в товарах

    Алгоритм:
        На вход принимается список ID товаров в измененном порядке,
        затем по порядку этих ID изменяется поле order_id в бд

    :param ids: список айдишников товаров из бд
    :return: True - успех / False - ошибка

    """
    if not len(ids) == await Product.all().count():
        return False

    products: list[Product] = []

    # провера на существование категорий с таким ID
    for id_ in ids:
        product = await Product.get_or_none(id=id_)
        if not product:
            return False

        products.append(product)

    for product, order_id in zip(products, range(1, len(products) + 1)):
        product.order_id = order_id

    await Product.bulk_update(products, fields=["order_id"])

    return True


async def change_parameter_order(ids: list[int]) -> bool:
    """
    смена порядка в параметрах

    Алгоритм:
        На вход принимается список ID параметров в измененном порядке,
        затем по порядку этих ID изменяется поле order_id в бд

    :param ids: список айдишников параметров из бд
    :return: True - успех / False - ошибка

    """
    parameters: list[Parameter] = []

    # провера на существование категорий с таким ID
    for id_ in ids:
        parameter = await Parameter.get_or_none(id=id_)
        if not parameter:
            return False

        parameters.append(parameter)

    for param, order_id in zip(parameters, range(1, len(parameters) + 1)):
        param.order_id = order_id

    await Parameter.bulk_update(parameters, fields=["order_id"])

    return True


async def get_items_data_for_order(
    parameter_id: int, count: int, order
) -> list[ProductData]:
    """получение данных по товару из заказа и удаление этих ключей из базы данных (архивирование)"""

    # завершаем заказ
    if not order.status == "finished":
        items = await ProductData.filter(
            parameter__id=parameter_id, is_active=True
        ).limit(count)

        # если количество товаров в базе меньше, чем запросил пользователь
        # ничего не возвращаем, кидаем на ручную оплату
        if len(items) < count:
            return []

        # деактивация товаров
        for item in items:
            await item.update_from_dict(
                {"is_active": False, "order_id": order.id}
            ).save()

        return items
    # берем из истории (уже купленные ключи)
    else:
        items = await ProductData.filter(
            order_id=order.id, parameter__id=parameter_id, is_active=False
        ).all()
        return items


async def get_items_data_for_product(product_id: int) -> QuerySet[ProductData]:
    """получение строк (файлов) по товарам из базы"""
    items = ProductData.filter(parameter__product_id=product_id, is_active=True).all()

    return items


async def update_parameter_data(parameter_id: int, data: list[str]):
    """обновление строк по товару (сверка и удаление старых, добавление новых)"""
    # модельки строк
    items = [
        u
        for u in await ProductData.filter(
            parameter__id=parameter_id, is_active=True
        ).all()
    ]
    # данные строк
    items_values = [v.value for v in items]

    new_ = []

    for item in data:
        if item not in items_values:
            # добавление нового товара, если его не было в бд
            new_.append(item)

        try:
            # удаление из списка строк из бд для дальнейшего удаления из бд
            items_values.remove(item)
        except ValueError:
            pass

    # удаление оставшихся строк
    await ProductData.filter(value__in=items_values, parameter_id=parameter_id).delete()

    # создание новых строк
    await ProductData.bulk_create(
        [ProductData(parameter_id=parameter_id, value=v) for v in new_]
    )
