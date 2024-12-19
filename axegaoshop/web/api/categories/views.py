from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.category import Category, change_category_order
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.categories.schema import (
    CategoryCreate,
    CategoryIn_Pydantic,
    CategoryUpdate,
)

router = APIRouter()


@router.post(
    "/categories",
    response_model=CategoryIn_Pydantic,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
)
async def category_create(category: CategoryCreate):
    cat = Category(title=category.title, photo=category.photo)
    await cat.save()

    return await CategoryIn_Pydantic.from_queryset_single(
        Category.filter(id=cat.id).first()
    )


@router.get("/categories", response_model=list[CategoryIn_Pydantic])
async def category_get():

    return await CategoryIn_Pydantic.from_queryset(Category.all())


@router.patch(
    "/category/{id}",
    response_model=CategoryIn_Pydantic,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
)
async def category_update(id: int, category_: CategoryUpdate):
    cat = await Category.get_or_none(id=id)

    if not cat:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Category.filter(id=id).update(**category_.model_dump(exclude_unset=True))

    return await CategoryIn_Pydantic.from_queryset_single(
        Category.filter(id=id).first()
    )


@router.delete(
    "/category/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def category_delete(id: int):
    cat = await Category.get_or_none(id=id)

    if not cat:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await Category.filter(id=id).delete()


@router.post(
    "/category/order",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
    response_model=list[CategoryIn_Pydantic],
)
async def change_category_order_router(category_ids: list[int]):
    res = await change_category_order(category_ids)

    if not res:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await CategoryIn_Pydantic.from_queryset(Category.all())
