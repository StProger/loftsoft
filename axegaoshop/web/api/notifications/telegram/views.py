import asyncio

from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.telegram_settings import (
    TelegramReciever,
    TelegramSetting,
    get_tg_recievers,
    get_tg_settings,
)
from axegaoshop.services.notifications.telegram import TelegramService
from axegaoshop.services.notifications.telegram.telegram_di import (
    check_valid,
    get_telegram_data,
)
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.notifications.telegram.schema import (
    TelegramSettingIn,
    TelegramSettingUpdate,
)

router = APIRouter()


@router.get(
    "/telegram/settings",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=TelegramSettingIn,
)
async def get_telegram_settings():
    telegram_settings = await get_tg_settings()
    recievers = await get_tg_recievers()

    if not telegram_settings:
        return TelegramSettingIn(
            token="", telegram_ids=[r.telegram_id for r in recievers]
        )

    return TelegramSettingIn(
        token=telegram_settings.token, telegram_ids=[r.telegram_id for r in recievers]
    )


@router.post(
    "/telegram/settings/test",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def test_notify_telegram(
    tg_service: TelegramService = Depends(get_telegram_data),
):
    """отправка тестового уведомления"""
    if not tg_service:
        raise HTTPException(404, detail="CONFIGURE_TELEGRAM_SETTINGS")

    await asyncio.create_task(tg_service.test_notify())


@router.post(
    "/telegram/settings",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def create_or_update_telegram_settings(data: TelegramSettingUpdate):
    """обновляет или созает данные по уведам в тг"""
    telegram_settings = await get_tg_settings()
    recievers = [r.telegram_id for r in await get_tg_recievers()]

    # проверка токена на валид
    if not await check_valid(data.token):
        raise HTTPException(status_code=400, detail="INVALID_TOKEN")

    # записей нет, создаем новую
    if not telegram_settings:
        await TelegramSetting.create(token=data.token)

    # обновление
    else:
        await TelegramSetting.filter(id=telegram_settings.id).update(token=data.token)

    for r in recievers:
        if r not in data.telegram_ids:
            await TelegramReciever.filter(telegram_id=r).delete()

    # создание получателей
    [
        await TelegramReciever.create(telegram_id=id_)
        for id_ in data.telegram_ids
        if id_ not in recievers
    ]


@router.delete(
    "/telegram/settings/reciever/{telegram_id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def delete_reciever(telegram_id: int):
    """удаление получателя рассылок (telegran_id - айди человека в телеге)"""
    reciever = await TelegramReciever.get_or_none(telegram_id=telegram_id)

    if not reciever:
        raise HTTPException(status_code=404, detail="RECIEVER_NOT_FOUND")

    await reciever.delete()
