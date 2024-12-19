from tortoise import fields
from tortoise.models import Model


class PaymentSettingsOzone(Model):
    """таблица с данными о платежке Sbp OzoneBank"""

    id = fields.IntField(pk=True)

    name = fields.TextField(null=True)  # название настройки (акка)

    token = fields.TextField(null=False)  # токен доступа к акку
    pin_code = fields.TextField(null=False)  # пинкод от лк

    created_datetime = fields.DatetimeField(auto_now_add=True)

    phone = fields.TextField()  # номер телефона от акка для переводов

    fio = fields.TextField()  # ФИО для перевода

    class Meta:
        table = "payment_settings_ozone"
        ordering = ["-created_datetime"]


async def get_ozone_bank_data() -> PaymentSettingsOzone | None:
    """получение актуальных платежных данных"""
    p_s_o = PaymentSettingsOzone.filter().all()

    if not await p_s_o.exists():
        return None

    return await p_s_o.first()
