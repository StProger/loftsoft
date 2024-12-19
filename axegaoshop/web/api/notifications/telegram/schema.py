from pydantic import BaseModel, model_validator


class TelegramSettingUpdate(BaseModel):
    token: str
    telegram_ids: list[int]


class TelegramSettingIn(BaseModel):
    token: str = ""
    telegram_ids: list[int]
