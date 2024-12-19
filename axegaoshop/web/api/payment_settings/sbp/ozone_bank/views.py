from fastapi import APIRouter, Depends, HTTPException

from axegaoshop.db.models.payment_settings import (
    PaymentSettingsOzone,
    get_ozone_bank_data,
)
from axegaoshop.services.payment.sbp.ozon_bank_di import get_ozone_bank_raw
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin
from axegaoshop.web.api.payment_settings.sbp.ozone_bank.schema import (
    PaymentSettingsCreate,
    PaymentSettingsIn,
    PaymentSettingsUser,
)

router = APIRouter()


@router.post(
    "/payments/sbp/ozon",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=201,
)
async def create_payment_setting_ozone_bank(payment_settings: PaymentSettingsCreate):
    """загрузка данных платежных для ЛК озон банка"""
    ozone_bank = await get_ozone_bank_raw(
        payment_settings.token, payment_settings.pin_code
    )

    if not ozone_bank:
        raise HTTPException(status_code=401, detail="INVALID_DATA")

    await PaymentSettingsOzone().create(
        **payment_settings.model_dump(exclude_unset=True)
    )


@router.get(
    "/payments/sbp/ozon",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=PaymentSettingsIn,
)
async def get_payment_settings_ozone_bank():
    """получение данных по озон банку для админов"""
    return PaymentSettingsIn.model_validate(await get_ozone_bank_data())


@router.get(
    "/payments/sbp/ozon/user",
    dependencies=[Depends(JWTBearer())],
    response_model=PaymentSettingsUser,
)
async def get_payment_settings_ozone_bank_user():
    """получение данных по озон банку для пользователей"""
    return PaymentSettingsUser.model_validate(await get_ozone_bank_data())
