import datetime
from dataclasses import dataclass

import aiohttp
from pydantic import BaseModel, Field, computed_field

OZONE_BASE_URL = "https://finance.ozon.ru"


@dataclass
class OzoneMethods:
    """методы API озона, которые используем"""

    AUTH_LOGIN: str = "/api/v2/auth_login"
    CLIENT_OPERATIONS: str = "/api/v2/clientOperations"


@dataclass
class EffectTypes:
    """тип платежей в истории (поступление, отправка)"""

    INPUT: str = "EFFECT_CREDIT"
    OUTPUT: str = "EFFECT_DEBIT"


class PaymentModel(BaseModel):
    """модель возвращаемого ответа от сервера Ozone Bank"""

    id: str
    operation_id: str = Field(str, alias="operationId")
    sender: str = Field(str, alias="purpose")  # отправитель
    pay_datetime: datetime.datetime = Field(alias="time")  # время платежа
    merchant_name: str = Field(str, alias="merchantName")  # банк отправителя
    status: str  # должен быть success
    amount_raw: int = Field(int, alias="accountAmount")

    @computed_field
    def amount(self) -> float:
        """computing amount in float, not raw(int) format"""
        return self.amount_raw / 100


class OzoneBank:
    """класс для работы с приватным API Ozone Bank-а

    - проверка платежей
    - идентификация платежа по копейкам
    """

    def __init__(self, pin_code: str, secure_refresh_token: str):
        self.pin_code: str = pin_code
        self.secure_refresh_token: str = secure_refresh_token

        self.obank_session_token: str | None = None

        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def prepare(self):
        """prepare settings data"""
        self.obank_session_token = await self.__refresh_obank_token()
        if not self.obank_session_token:
            return None

        return self

    async def __get_refresh_cookies(self) -> dict:
        """getting cookies for refreshing access token"""
        return {"__Secure-refresh-token": self.secure_refresh_token}

    async def __refresh_obank_token(self) -> str | None:
        """
        refreshing ozone bank token for accessing ozone bank
        :return:
            token - success
            None - invalid data
        """
        json_data = {
            "pincode": "1593",
        }
        async with aiohttp.ClientSession(
            cookies=await self.__get_refresh_cookies(), headers=self.headers
        ) as session:
            async with session.post(
                url=OZONE_BASE_URL + OzoneMethods.AUTH_LOGIN, json=json_data
            ) as response:

                if response.status == 200:
                    for value in response.headers.values():
                        if "__OBANK_session" in value:
                            token = value.split("=")[1].split(";")[0].strip()
                            return token
                else:
                    return None

    async def is_valid(self) -> bool:
        """:TODO: проверка отвала озона"""
        ...

    async def __get_auth_cookies(self) -> dict:
        """getting every request cookies"""
        return {"__OBANK_session": self.obank_session_token}

    async def __get_client_operations(self) -> list[PaymentModel] | None:
        """get payment history"""
        json_data = {
            "cursors": {
                "next": None,
                "prev": None,
            },
            "perPage": 100,
            "filter": {
                "categories": [],
                "effect": EffectTypes.INPUT,
            },
        }
        async with aiohttp.ClientSession(
            cookies=await self.__get_auth_cookies()
        ) as session:
            async with session.post(
                url=OZONE_BASE_URL + OzoneMethods.CLIENT_OPERATIONS, json=json_data
            ) as response:
                if response.status == 200:
                    response_json = await response.json(content_type=None)

                    return [
                        PaymentModel.model_validate(data)
                        for data in response_json["items"]
                    ]
                else:
                    return None

    async def has_payment(self, total_sum: float, datetime_from: datetime) -> bool:
        """провера на то, что платеж с заданной суммой есть в истории"""
        client_operations = await self.__get_client_operations()

        if not client_operations:
            return False

        client_operations = filter(
            (lambda x: x.pay_datetime > datetime_from), client_operations
        )
        for client_operation in client_operations:

            if str(client_operation.amount) == str(total_sum):
                return True

        return False
