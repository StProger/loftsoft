import asyncio
import typing
from datetime import datetime
from typing import Annotated

import pytz
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from axegaoshop.db.models.order import Order
from axegaoshop.db.models.password_reset import PasswordReset
from axegaoshop.db.models.replenish import Replenish
from axegaoshop.db.models.token import Token
from axegaoshop.db.models.user import User
from axegaoshop.services.image.avatar import create_user_photo
from axegaoshop.services.notifications.mailing.mailing import Mailer
from axegaoshop.services.payment.sbp.ozon_bank import OzoneBank
from axegaoshop.services.payment.sbp.ozon_bank_di import get_ozone_bank
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.tools import (
    create_access_token,
    create_refresh_token,
    generate_password_drop_link,
    get_hashed_password,
    verify_password,
)
from axegaoshop.services.security.users import current_user_is_admin, get_current_user
from axegaoshop.settings import executor, settings
from axegaoshop.web.api.orders.schema import OrderIn_Pydantic
from axegaoshop.web.api.tokens.schema import TokenCreated, TokenRequest
from axegaoshop.web.api.users.schema import (
    UserCart_Pydantic,
    UserCreate,
    UserDropPassword,
    UserForAdmin_Pydantic,
    UserIn_Pydantic,
    UserOutput,
    UserReplenish_Pydantic,
    UserReplenishBalance,
    UserReplenishOut,
    UserUpdate,
    UserUpdateAdmin,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


class Message(BaseModel):
    message: str


@router.post(
    "/user/register",
    status_code=201,
    # response_model=UserOutput,
    responses={
        400: {"model": Message, "description": "User with such login already exists."}
    },
)
async def register_user(
    user: UserCreate, user_check: Annotated[User | None, Depends(get_current_user)]
):
    user_exists: bool = await User.filter(username=user.username).exists()

    if user_exists:
        raise HTTPException(status_code=401, detail="LOGIN_EXISTS")

    if user.email:
        email_exists: bool = await User.filter(
            email__iexact=user.email.strip()
        ).exists()

        if email_exists:
            raise HTTPException(status_code=401, detail="EMAIL_EXISTS")

    if not user.password and user_exists:
        await User.filter(id=user_check.id).update(
            **user.model_dump(exclude_unset=True), is_anonymous=False
        )

        return User.filter(id=user_check.id).first()

    elif not user_exists and not user.email and not user.password:
        new_user = User(username=user.username, is_anonymous=True)
        await new_user.save()

        access = create_access_token(new_user.id)
        refresh = create_refresh_token(new_user.id)

        token_db = Token(
            access_token=access, refresh_token=refresh, user_id=new_user.id
        )
        await token_db.save()

        return token_db

    encrypted_password = get_hashed_password(user.password)

    new_user = User(
        username=user.username,
        password=encrypted_password,
        email=user.email.lower().strip(),
    )
    new_user.photo = create_user_photo(user.username)
    await new_user.save()

    return new_user


@router.post("/user/login", response_model=TokenCreated)
async def login_user(request: TokenRequest):
    """
    для получения access token для анонима (неавторизованного человека) передать username без пароля
    """
    user = await User.filter(email__iexact=request.email.strip()).get_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not request.password and user.is_anonymous:
        access = create_access_token(user.id)
        refresh = create_refresh_token(user.id)

        token_db = Token(access_token=access, refresh_token=refresh, user_id=user.id)
        await token_db.save()

        return token_db

    if not request.password:
        raise HTTPException(status_code=401, detail="Provide password")

    hashed_password: str = user.password

    if not verify_password(request.password, hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    token_db = Token(access_token=access, refresh_token=refresh, user_id=user.id)
    await token_db.save()

    return token_db


@router.get(
    "/user/me", dependencies=[Depends(JWTBearer())], response_model=UserCart_Pydantic
)
async def get_current_user_(user: Annotated[User, Depends(get_current_user)]):
    return await UserCart_Pydantic.from_queryset_single(User.filter(id=user.id).first())


@router.get(
    "/user/orders",
    dependencies=[Depends(JWTBearer())],
    response_model=list[OrderIn_Pydantic],
)
async def get_user_orders(user: Annotated[User, Depends(get_current_user)]):
    """получение истории заказов пользователя (текущего)"""
    if user.is_anonymous:
        raise HTTPException(status_code=404, detail="AUTHORIZE_REQUIRED")

    return await OrderIn_Pydantic.from_queryset(
        Order.filter(user_id=user.id, status="finished").all()
    )


@router.get(
    "/user/orders/{order_id}",
    dependencies=[Depends(JWTBearer())],
    # response_model=list[OrderIn_Pydantic]
)
async def get_user_order_by_id(
    order_id: int, user: Annotated[User, Depends(get_current_user)]
):
    """получение инфы по заказу пользователя (текущего)"""
    if user.is_anonymous:
        raise HTTPException(status_code=404, detail="AUTHORIZE_REQUIRED")

    res_: list[dict] = []
    for order in await Order.filter(user=user, status="finished").all():
        res_.append(await order.get_items(finished=True))

    for r in res_:
        if r["id"] == order_id:
            return r

    return None


@router.get(
    "/user/replenishes",
    dependencies=[Depends(JWTBearer())],
    response_model=list[UserReplenish_Pydantic],
)
async def get_user_replenishes(user: Annotated[User, Depends(get_current_user)]):
    """получение истории пополнений пользователя (текущего)"""
    if user.is_anonymous:
        raise HTTPException(status_code=404, detail="AUTHORIZE_REQUIRED")

    return await UserReplenish_Pydantic.from_queryset(
        Replenish.filter(user_id=user.id, status="finished").all()
    )


@router.get(
    "/user/{id}",
    response_model=UserCart_Pydantic,
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
)
async def get_user_by_id(id: int):
    if not await User.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    return await UserCart_Pydantic.from_queryset_single(User.filter(id=id).first())


@router.patch(
    "/user/me", dependencies=[Depends(JWTBearer())], response_model=UserOutput
)
async def update_current_user(
    user: UserUpdate, user_data: Annotated[User, Depends(get_current_user)]
):

    # логин недоступен
    if user.username and await User.get_or_none(username=user.username):
        raise HTTPException(status_code=401, detail="LOGIN_ALREADY_EXISTS")

    await User.filter(id=user_data.id).update(**user.model_dump(exclude_unset=True))

    return await User.filter(id=user_data.id).first()


@router.delete(
    "/user/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[UserForAdmin_Pydantic],
    status_code=200,
)
async def delete_user(id: int):
    user = await User.get_or_none(id=id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    await user.delete()

    return await UserForAdmin_Pydantic.from_queryset(User.all().limit(20).offset(0))


@router.patch(
    "/user/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=UserIn_Pydantic,
)
async def update_user_by_id(id: int, user: UserUpdateAdmin):

    # пользователь не найден
    if not await User.get_or_none(id=id):
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    # логин недоступен
    if user.username and await User.get_or_none(username=user.username):
        raise HTTPException(status_code=401, detail="LOGIN_ALREADY_EXISTS")

    if user.password:
        user.password = get_hashed_password(user.password)

    await User.filter(id=id).update(**user.model_dump(exclude_unset=True))

    return await UserIn_Pydantic.from_queryset_single(User.filter(id=id).first())


@router.get(
    "/users",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[UserForAdmin_Pydantic],
)
async def get_users(
    query: typing.Optional[str] = None, limit: int = 20, offset: int = 0
):
    """
    Поиск пользователей в базе данных для админа:

    *query* - вхождение подстроки (startswith) в email (не чувствителен к регистру)
    """
    if not query:
        return await UserForAdmin_Pydantic.from_queryset(
            User.all().limit(limit).offset(offset)
        )

    else:
        return await UserForAdmin_Pydantic.from_queryset(
            User.filter(email__istartswith=query).limit(limit).offset(offset)
        )


@router.post(
    "/user/balance/replenish",
    status_code=200,
    dependencies=[Depends(JWTBearer())],
    response_model=UserReplenishOut,
)
async def replenish_balance(
    replenish_data: UserReplenishBalance, user: User = Depends(get_current_user)
):
    replenish = Replenish(payment_type=replenish_data.payment_type, user_id=user.id)
    await replenish.save()

    await replenish.set_result_price(replenish_data.amount)

    await replenish.refresh_from_db()

    return UserReplenishOut(
        number=replenish.number,
        result_price=replenish.result_price,
        payment_type=replenish.payment_type,
        status=replenish.status,
        created_datetime=replenish.created_datetime,
    )


@router.get(
    "/user/balance/replenish/{number}",
    dependencies=[Depends(JWTBearer())],
    status_code=200,
)
async def replenish_balance_check(
    number: str,
    user: User = Depends(get_current_user),
    ozone_bank: OzoneBank = Depends(get_ozone_bank),
):
    if not ozone_bank:
        raise HTTPException(status_code=500, detail="SERVER_ERROR")

    replenish = await Replenish.get_or_none(number=number, user_id=user.id)

    if not replenish or replenish.status in ["canceled", "finished"]:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    check = await ozone_bank.has_payment(
        replenish.result_price, replenish.created_datetime
    )

    if check:
        await user.add_balance(replenish.result_price)
        await replenish.finish()

    return {
        "number": replenish.number,
        "result_price": replenish.result_price,
        "payment_type": replenish.payment_type,
        "status": replenish.status,
        "created_datetime": replenish.created_datetime,
        "remaining_time": 600
        - ((datetime.now(tz=pytz.UTC) - replenish.created_datetime).total_seconds()),
    }


@router.post(
    "/user/password/drop",
    status_code=200,
)
async def drop_password(request: Request, user_drop_password: UserDropPassword):
    """:TODO: send email with generated link & :TODO: base url change logic!!!"""
    user = await User.get_or_none(email=user_drop_password.email)

    if not user:
        raise HTTPException(status_code=404, detail="EMAIL_NOT_FOUND")

    password_reset = await PasswordReset.create(
        email=user_drop_password.email,
        hashed_password=get_hashed_password(user_drop_password.password),
    )

    password_drop_path: str = generate_password_drop_link(password_reset.id)

    password_drop_link: str = str(settings.base_hostname) + password_drop_path

    mailer = Mailer(recipient=user.email)

    executor.submit(mailer.send_reset(reset_url=password_drop_link))


@router.get("/user/password/reset/{uid}", status_code=200)
async def reset_password_from_email(uid: str):
    """переход по ссылке в письме и автоматическая смена пароля"""
    password_reset = await PasswordReset.get_or_none(id=uid)

    # если нет такого запроса на сброс пароля или он деактивирован
    if not password_reset or not password_reset.is_active:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    user = await User.get_or_none(email=password_reset.email)
    if not user:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    # обновление пароля
    await user.update_from_dict({"password": password_reset.hashed_password}).save()

    # деактивация ссылки
    password_reset.is_active = False
    await password_reset.save()

    return RedirectResponse(settings.front_hostname + "/auth")
