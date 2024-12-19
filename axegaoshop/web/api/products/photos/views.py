from fastapi import APIRouter, Depends, HTTPException
from tortoise.expressions import Q

from axegaoshop.db.models.product import Product, ProductPhoto
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.products.photos.schema import (
    PhotoCreate,
    PhotoIn_Pydantic,
    PhotoUpdate,
)

router = APIRouter()


@router.get(path="/product/{id}/photos", response_model=list[PhotoIn_Pydantic])
async def get_product_photo(id: int):
    if not await Product.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await PhotoIn_Pydantic.from_queryset(ProductPhoto.filter(product_id=id))


@router.post(
    path="/product/{id}/photos",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=PhotoIn_Pydantic,
)
async def create_product_photo(id: int, photo: PhotoCreate):
    if not await Product.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    photo_ = ProductPhoto(photo=photo.photo, product_id=id)

    await photo_.save()

    return photo_


@router.patch(
    path="/photo/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=PhotoIn_Pydantic,
)
async def update_product_photo(id: int, photo: PhotoUpdate):
    """передавать айди фотографии"""
    photo_db = await ProductPhoto.get_or_none(id=id)
    if not photo_db:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    if photo.main:
        await ProductPhoto.filter(
            Q(Q(main=True) & Q(product_id=photo_db.product_id))
        ).update(main=False)

    await ProductPhoto.filter(id=id).update(**photo.model_dump(exclude_unset=True))

    return await ProductPhoto.filter(id=id).first()


@router.delete(
    path="/photo/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def delete_product_photo(id: int):
    if not await ProductPhoto.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    await ProductPhoto.filter(id=id).delete()
