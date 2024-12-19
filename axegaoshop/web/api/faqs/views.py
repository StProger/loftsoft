from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.faq import Faq, change_faq_order
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.faqs.schema import (
    FaqPydanticAdmin,
    FaqPydanticAdminCreate,
    FaqPydanticDb,
    FaqPydanticUser,
    Faqs_Pydantic,
)

router = APIRouter()


@router.post(
    "/faq",
    response_model=list[Faqs_Pydantic],
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
)
async def faqs_manipulate(faqs: list[FaqPydanticAdminCreate]):
    """изменение/удаление/редактировение пользовательских соглашений"""
    faqs_in_db: list[FaqPydanticDb] = []
    for faq_db in await Faq.all():
        faqs_in_db.append(
            FaqPydanticDb(
                id=faq_db.id,
                content=faq_db.content,
                title=faq_db.title,
                slug=faq_db.slug,
            )
        )

    for faq in faqs:
        faq_existing: list[FaqPydanticDb] = list(
            filter(lambda x: x.title == faq.title, faqs_in_db)
        )
        if faq_existing:
            faq_existing: FaqPydanticDb = faq_existing[0]
            if faq.content != faq_existing.content:
                await Faq.filter(id=faq_existing.id).update(content=faq.content)

            continue
        else:
            await Faq.create(
                **faq.model_dump(exclude_unset=True),
            )

            continue

    for faq in faqs_in_db:
        faq_existing_to_delete: list[FaqPydanticUser] = list(
            filter(lambda x: x.title == faq.title, faqs)
        )

        if not faq_existing_to_delete:
            await Faq.filter(title=faq.title).delete()

    return await Faqs_Pydantic.from_queryset(Faq.all())


@router.get("/faq", response_model=list[Faqs_Pydantic])
async def faq_get():
    return await Faqs_Pydantic.from_queryset(Faq.all())


@router.post(
    "/faq/order",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
    response_model=list[Faqs_Pydantic],
)
async def change_faq_order_router(faq_ids: list[int]):
    res = await change_faq_order(faq_ids)

    if not res:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await Faqs_Pydantic.from_queryset(Faq.all())
