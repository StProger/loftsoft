from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.order import Order
from axegaoshop.db.models.product import Product
from axegaoshop.db.models.review import Review, ReviewPhoto
from axegaoshop.db.models.user import User
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin, get_current_user
from axegaoshop.web.api.reviews.schema import (
    ReviewCreate,
    ReviewIn_Pydantic,
    ReviewOutput,
    ReviewUpdate,
)
from axegaoshop.web.api.users.schema import UserProductsComment

router = APIRouter()


async def get_reviews(
    status: str = "accepted", limit: int = 20, offset: int = 0
) -> list[ReviewOutput]:
    """
    функия для получения отзывов из бд по параметру status:
        - accepted
        - wait_for_accept
    """
    return [
        ReviewOutput(
            id=r.id,
            images=[photo.photo for photo in r.review_photos],
            rate=r.rate,
            text=r.text,
            product=r.product.title,
            user=r.user.username if r.user else None,
            user_photo=r.user.photo,
            created_datetime=r.approved_datetime,
        )
        for r in (
            await Review.filter(status=status)
            .prefetch_related("review_photos", "product", "user")
            .all()
            .limit(limit)
            .offset(offset)
            .order_by("created_datetime")
        )
    ]


@router.post(
    "/reviews/available",
    dependencies=[Depends(JWTBearer())],
    response_model=list[UserProductsComment],
)
async def get_available_reviews_products(user: User = Depends(get_current_user)):
    """получение доступных для написания отзывов товаров"""

    return [
        UserProductsComment(product_id=p[0], title=p[1], order_id=p[2])
        for p in await user.get_available_products_to_comment()
    ]


@router.post("/reviews", dependencies=[Depends(JWTBearer())], status_code=201)
async def create_review(
    review_data: ReviewCreate, user: User = Depends(get_current_user)
):
    """отправка отзыва (на модерацию)"""
    order = await Order.get_or_none(id=review_data.order_id)

    if not order:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")

    if not (await order.user.get_or_none()).id == user.id:
        raise HTTPException(status_code=404, detail="FORIBDDEN")

    if not await Product.get_or_none(id=review_data.product_id):
        raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")

    if review_data.product_id not in await order.get_order_products():
        raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")

    if not await order.review_available(review_data.product_id):
        raise HTTPException(status_code=401, detail="NOT_AVAILABLE")

    review = await Review.create(
        rate=review_data.rate,
        text=review_data.text,
        user=user,
        order_id=review_data.order_id,
        product_id=review_data.product_id,
    )

    if review_data.images:
        for photo in review_data.images:
            await ReviewPhoto.create(review=review, photo=photo)


@router.get(
    "/reviews/unaccepted",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[ReviewOutput],
)
async def get_unaccepted_reviews(limit: int = 20, offset: int = 0):
    return await get_reviews(status="wait_for_accept", limit=limit, offset=offset)


@router.get("/reviews", response_model=list[ReviewOutput])
async def get_reviews_handler(limit: int = 20, offset: int = 0):
    return await get_reviews("accepted", limit, offset)


@router.patch(
    "/reviews/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def update_review(id: int, review_update: ReviewUpdate):
    review = await Review.get_or_none(id=id)

    if not review:
        raise HTTPException(status_code=404, detail="REVIEW_NOT_FOUND")

    await review.update_from_dict({"text": review_update.text})
    await review.save()


@router.delete(
    "/review/{review_id}/photo/{photo_id}",
    response_model=ReviewIn_Pydantic,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
)
async def delete_review_photo(review_id: int, photo_id: int):
    review = await Review.get_or_none(id=review_id)

    if not review:
        raise HTTPException(status_code=404, detail="REVIEW_NOT_FOUND")

    photo = await ReviewPhoto.get_or_none(id=photo_id)

    if not photo:
        raise HTTPException(status_code=404, detail="PHOTO_NOT_FOUND")

    await photo.delete()

    await review.refresh_from_db()

    return await ReviewIn_Pydantic.from_tortoise_orm(review)


@router.post(
    "/review/{id}/accept",
    status_code=200,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[ReviewOutput],
)
async def accept_review(id: int):
    """принятие отзыва"""
    review = await Review.get_or_none(id=id)

    if not review:
        raise HTTPException(status_code=404, detail="REVIEW_NOT_FOUND")

    await review.set_status("accepted")

    return await get_reviews("accepted")


@router.post(
    "/review/{id}/decline",
    status_code=200,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[ReviewOutput],
)
async def decline_review(id: int):
    """отклонение отзыва"""
    review = await Review.get_or_none(id=id)

    if not review:
        raise HTTPException(status_code=404, detail="REVIEW_NOT_FOUND")

    await review.set_status("declined")

    return await get_reviews("wait_for_accept")
