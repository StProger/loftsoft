from tortoise import fields
from tortoise.models import Model

from axegaoshop.db.models.product import Parameter, Product
from axegaoshop.db.models.user import User


class ShopCart(Model):

    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        model_name="axegaoshop.User", related_name="shop_cart"
    )
    product = fields.ForeignKeyField("axegaoshop.Product", related_name="shop_cart")
    parameter = fields.ForeignKeyField("axegaoshop.Parameter", related_name="shop_cart")
    quantity = fields.IntField(default=1)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "shop_cart"
        ordering = ["created_at"]

    class PydanticMeta:
        exclude = ("user", "user_id")


async def add_to_cart(
    user_id: int, product_id: int, parameter_id: int, quantity: int
) -> ShopCart:
    user = await User.filter(id=user_id).first().prefetch_related("shop_cart")
    product = await Product.filter(id=product_id).first()
    parameter = await Parameter.filter(id=parameter_id).first()

    _cart = await ShopCart.filter(
        product=product, user=user, parameter=parameter
    ).first()

    if not _cart:
        _cart = await ShopCart.create(
            user=user, product=product, parameter=parameter, quantity=quantity
        )

    else:
        if quantity <= 0:
            await _cart.delete()

        else:
            await _cart.update_from_dict({"quantity": quantity})
            await _cart.save()

    return _cart
