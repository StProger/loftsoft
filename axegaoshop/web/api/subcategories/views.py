from fastapi import APIRouter, Depends, HTTPException
from tortoise.functions import Count

from axegaoshop.db.models.category import Category
from axegaoshop.db.models.subcategory import Subcategory, change_subcategory_order
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.subcategories.schema import (
    SubcategoryCreate,
    SubcategoryIn_Pydantic,
    SubcategoryOrderChange,
    SubcategoryUpdate,
)

router = APIRouter()


@router.post(
    "/subcategories",
    response_model=SubcategoryIn_Pydantic,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
)
async def subcategory_create(subcategory: SubcategoryCreate):
    category = Category.filter(id=subcategory.category_id)

    if not await category.exists():
        raise HTTPException(status_code=404, detail="CATEGORY_NOT_FOUND")

    subcat = Subcategory(title=subcategory.title, category_id=subcategory.category_id)
    await subcat.save()

    return await SubcategoryIn_Pydantic.from_queryset_single(
        Subcategory.filter(id=subcat.id).first()
    )


@router.get(
    "/subcategories",
    response_model=list[SubcategoryIn_Pydantic],
)
async def subcategories_get(empty_filter: bool = True):
    """empty filter - если True, возвращает толкьо подкатегории, в которых есть товары
    False - возвращает все подкатегории"""
    if empty_filter:
        return await SubcategoryIn_Pydantic.from_queryset(
            Subcategory.annotate(product_count=Count("products"))
            .filter(product_count__not=0)
            .all()
        )
    else:
        return await SubcategoryIn_Pydantic.from_queryset(Subcategory.all())


@router.get("/subcategory/{id}", response_model=SubcategoryIn_Pydantic)
async def subcategory_get(id: int):
    subcategory = await Subcategory.get_or_none(id=id)
    if not subcategory:
        raise HTTPException(status_code=404, detail="CATEGORY_NOT_FOUND")

    return await SubcategoryIn_Pydantic.from_tortoise_orm(subcategory)


@router.get(
    "/category/{category_id}/subcategories", response_model=list[SubcategoryIn_Pydantic]
)
async def category_subcategory_get(category_id: int):
    if not await Category.get_or_none(id=category_id):
        raise HTTPException(status_code=404, detail="CATEGORY_NOT_FOUND")
    return await SubcategoryIn_Pydantic.from_queryset(
        Subcategory.filter(category_id=category_id).all()
    )


@router.patch(
    "/subcategory/{id}",
    response_model=SubcategoryIn_Pydantic,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
)
async def subcategory_update(id: int, subcategory_: SubcategoryUpdate):
    subcat = await Subcategory.get_or_none(id=id)

    if not subcat:
        raise HTTPException(status_code=404, detail="SUBCATEGORY_NOT_FOUND")

    if subcategory_.category_id:
        if not await Category.get_or_none(id=subcategory_.category_id):
            raise HTTPException(status_code=404, detail="CATEGORY_NOT_FOUND")

    await Subcategory.filter(id=id).update(
        **subcategory_.model_dump(exclude_unset=True)
    )

    return await SubcategoryIn_Pydantic.from_queryset_single(
        Subcategory.filter(id=id).first()
    )


@router.delete(
    "/subcategory/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def subcategory_delete(id: int):
    subcat = await Subcategory.get_or_none(id=id)

    if not subcat:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Subcategory.filter(id=id).delete()


@router.post(
    "/subcategory/order",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
    response_model=list[SubcategoryIn_Pydantic],
)
async def change_subcategory_order_router(subcat_ids: list[int]):
    res = await change_subcategory_order(subcat_ids)

    if not res:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await SubcategoryIn_Pydantic.from_queryset(Subcategory.all())
