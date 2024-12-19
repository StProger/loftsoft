import datetime

from pydantic import BaseModel


class PaymentSettingsCreate(BaseModel):
    token: str
    pin_code: str
    phone: str
    fio: str


class PaymentSettingsIn(BaseModel):
    token: str
    pin_code: str
    phone: str
    fio: str
    created_datetime: datetime.datetime

    class Config:
        from_attributes = True


class PaymentSettingsUser(BaseModel):
    phone: str
    fio: str

    class Config:
        from_attributes = True
