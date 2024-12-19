import typing

from fastapi import APIRouter, Depends, HTTPException
from tortoise.expressions import Q
from tortoise.functions import Avg, Coalesce
from transliterate import translit

from axegaoshop.db.models.product import (
    Option,
    Parameter,
    Product,
    ProductData,
    ProductPhoto,
    change_product_order,
)
from axegaoshop.db.models.review import Review
from axegaoshop.db.models.subcategory import Subcategory
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.products.schema import (
    ProductCreate,
    ProductDataOut,
    ProductIn_Pydantic,
    ProductUpdate,
)

router = APIRouter()


def transliterate_query(query: str) -> str:
    query = query.lower()
    return (
        translit(query, "ru", reversed=True)
        if "вин" not in query
        else (translit(query, "ru", reversed=True).replace("v", "w"))
    )


@router.get("/products", status_code=200, response_model=list[ProductIn_Pydantic])
async def get_products(
    price_sort: typing.Optional[bool] = None,
    rating_sort: typing.Optional[bool] = None,
    sale_sort: typing.Optional[bool] = None,
    query: typing.Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    Поиск карточек товара в базе данных для админа и пользователей:

    *query* - вхождение (startswith) в title (название) товара (не чувствителен к регистру)

    если *price_sort*, *rating_sort*, *sale_sort* не переданы, используется стандартный order, заданный админом

    *price_sort*, *rating_sort*, *sale_sort* могут принимать значения true/false или просто их не указывать
    """

    if not query:

        sorted_products = (
            Product.filter().all().prefetch_related().limit(limit).offset(offset)
        )
        if price_sort:
            price_sort = "card_price"
        elif not price_sort:
            price_sort = "-card_price"
        elif price_sort is None:
            price_sort = ""

        if rating_sort:
            rating_sort = "reviews_avg"
        elif not rating_sort:
            rating_sort = "-reviews_avg"
        elif rating_sort is None:
            rating_sort = ""

        sortings = [
            price_sort if price_sort else None,
            rating_sort if rating_sort else None,
        ]
        sortings = list(filter(lambda x: x is not None, sortings))

        if price_sort or rating_sort:
            sorted_products = sorted_products.annotate(
                reviews_avg=Coalesce(
                    Avg(
                        "parameters__order_parameters__order__reviews__rate",
                        _filter=(
                            Q(
                                Q(
                                    parameters__order_parameters__order__reviews__status="accepted"
                                )
                            )
                        ),
                    ),
                    0,
                )
            ).order_by(*sortings)

        sorted_products = (
            sorted_products.filter(card_has_sale=True) if sale_sort else sorted_products
        )

        rev = await Review.filter(status="accepted").values_list(
            "product_id", flat=True
        )

        result_ = []

        for value in await sorted_products.all():
            if value.id not in rev:
                value.reviews_avg = 0
                result_.append(value)
            else:
                result_.append(value)

        if len(result_) > 0 and hasattr(result_[0], "reviews_avg"):
            result_ = sorted(result_, key=lambda x: x.reviews_avg)

        return [await ProductIn_Pydantic.from_tortoise_orm(u) for u in result_]
    else:
        trans_query: str = transliterate_query(query)
        return await ProductIn_Pydantic.from_queryset(
            Product.filter(
                Q(title__istartswith=query) | Q(title__istartswith=trans_query)
            )
            .limit(limit)
            .offset(offset)
        )


@router.get(
    "/product/{id}/data",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[ProductDataOut],
)
async def items_by_product_get(id: int):
    """получение данных по товарам (строк) для админки"""
    if not await Product.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    parameters_all = Parameter.filter(product_id=id)

    response_data = []

    for parameter in await parameters_all.all():
        parameter_id = parameter.id
        items = await ProductData.filter(
            parameter_id=parameter_id, parameter__give_type__not="hand", is_active=True
        ).values("value")
        items_list = [item["value"] for item in items]
        response_data.append(
            ProductDataOut(parameter_id=parameter_id, items=items_list)
        )

    return response_data


@router.patch(
    "/product/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=ProductIn_Pydantic,
)
async def update_product(id: int, data: ProductUpdate):
    """обновление данных о товаре (только данных о товаре)"""
    if not await Product.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Product.filter(id=id).update(**data.model_dump(exclude_unset=True))

    return await ProductIn_Pydantic.from_queryset_single(Product.filter(id=id).first())


@router.get(
    "/subcategory/{subcategory_id}/products", response_model=list[ProductIn_Pydantic]
)
async def subcategory_products_get(
    subcategory_id: int,
    price_sort: typing.Optional[bool] = None,
    rating_sort: typing.Optional[bool] = None,
    sale_sort: typing.Optional[bool] = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    Получение товаров из подкатегории

    если *price_sort*, *rating_sort*, *sale_sort* не переданы, используется стандартный order, заданный админом

    *price_sort*, *rating_sort*, *sale_sort* могут принимать значения true/false или просто их не указывать
    """
    if not await Subcategory.get_or_none(id=subcategory_id):
        raise HTTPException(status_code=404, detail="SUBCATEGORY_NOT_FOUND")

    sorted_products = (
        Product.filter(subcategory_id=subcategory_id)
        .all()
        .prefetch_related()
        .limit(limit)
        .offset(offset)
    )
    if price_sort:
        price_sort = "card_price"
    elif not price_sort:
        price_sort = "-card_price"
    elif price_sort is None:
        price_sort = ""

    if rating_sort:
        rating_sort = "reviews_avg"
    elif not rating_sort:
        rating_sort = "-reviews_avg"
    elif rating_sort is None:
        rating_sort = ""

    sortings = [
        price_sort if price_sort else None,
        rating_sort if rating_sort else None,
    ]
    sortings = list(filter(lambda x: x is not None, sortings))

    if price_sort or rating_sort:
        sorted_products = sorted_products.annotate(
            reviews_avg=Coalesce(
                Avg(
                    "parameters__order_parameters__order__reviews__rate",
                    _filter=(
                        Q(
                            Q(
                                parameters__order_parameters__order__reviews__status="accepted"
                            )
                        )
                    ),
                ),
                0,
            )
        ).order_by(*sortings)

    sorted_products = (
        sorted_products.filter(card_has_sale=True) if sale_sort else sorted_products
    )

    rev = await Review.filter(status="accepted").values_list("product_id", flat=True)

    result_ = []

    for value in await sorted_products.all():
        if value.id not in rev:
            value.reviews_avg = 0
            result_.append(value)
        else:
            result_.append(value)

    # if len(result_) > 0 and hasattr(result_[0], "reviews_avg"):
    #     result_ = sorted(result_, key=lambda x: x.reviews_avg)

    return [await ProductIn_Pydantic.from_tortoise_orm(u) for u in result_]


@router.post(
    "/product/",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=201,
)
async def create_product(product_data: ProductCreate):
    """
    *give_type* - тип выдачи.
      - string - обычные строки
      - file - файлы
      - hand - ручная выдача из админки

    Если тип выдачи *string* - грузим так же, как и в примере.

    Если тип выдачи *file* требуется сначала загрузить файлы в /api/upload
    и результат передать в качестве параметров

    Если тип выдачи *hand* можно исключить ['parameters']['data'] из запроса на создание товара
    """
    photos_ = product_data.photos
    options_ = product_data.options
    parameters_ = product_data.parameters

    subcategory = await Subcategory.filter(id=product_data.subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="SUBCATEGORY_NOT_FOUND")

    product = Product(
        title=product_data.title,
        description=product_data.description,
        card_price=product_data.card_price,
        card_has_sale=parameters_[0].has_sale,
        card_sale_price=float(parameters_[0].sale_price),
        subcategory=subcategory,
    )

    await product.save()
    parameters = [
        Parameter(
            title=p.title,
            description=p.description,
            price=p.price,
            has_sale=p.has_sale,
            give_type=p.give_type,
            sale_price=float(p.sale_price),
            product=product,
        )
        for p in parameters_
    ]

    param_cache = []

    for param in parameters:
        await param.save()
        param_cache.append(param)

    for param_idx, p in enumerate(parameters_, start=0):
        for d in p.data:
            p_d = ProductData(parameter=param_cache[param_idx], value=d)
            await p_d.save()

    if options_:
        options = [
            Option(title=o.title, value=o.value, is_pk=o.is_pk, product=product)
            for o in options_
        ]

        # saving options
        if all([await opt.is_available() for opt in options]):
            for opt in options:
                await opt.save()

    # добавление фото товара и назначение первой фотографии main
    product_photo = [
        ProductPhoto(photo=pp, product=product, main=True if idx == 0 else False)
        for idx, pp in enumerate(photos_, start=0)
    ]

    for pht in product_photo:
        await pht.save()

    return {"id": product.id}


@router.get("/product/{id}", response_model=ProductIn_Pydantic)
async def get_product(id: int):
    product_ = await Product.get_or_none(id=id)

    if not product_:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await ProductIn_Pydantic.from_queryset_single(Product.get(id=id))


@router.delete(
    "/product/{id}", description="Delete product and all related data", status_code=200
)
async def delete_product(id: int):
    product_ = await Product.get_or_none(id=id)

    if not product_:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await product_.delete()


@router.post(
    "/product/order",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def change_product_order_router(product_ids: list[int]):
    res = await change_product_order(product_ids)

    if not res:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
