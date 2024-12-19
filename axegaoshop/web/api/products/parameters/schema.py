import typing

from pydantic import BaseModel, model_validator
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.product import Parameter

#
# class ParameterDataCreate(BaseModel):
#     value: str


class ParameterCreate(BaseModel):
    title: str
    description: typing.Optional[str] = None
    price: float
    give_type: typing.Literal["hand", "file", "string"]
    has_sale: bool = False
    sale_price: str = "0.0"
    data: typing.Optional[list[str]] = []

    @model_validator(mode="after")
    def validate_param_create(self) -> "ParameterCreate":
        if self.sale_price == "":
            self.sale_price = "0.0"
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Windows 11 Professional",
                    "price": 4500,
                    "descripition": "Описание параметра",
                    "has_sale": False,
                    "give_type": "string",
                    "data": [
                        "FWBFIWEF-FWEF-W-EFWE-F-WE",
                        "QWEQE-QEQWEQW-EQWEQWEQW-GERGRE",
                    ],
                }
            ]
        }
    }


class ParameterUpdate(BaseModel):
    title: str
    price: float
    has_sale: bool = False
    sale_price: float = 0.0
    give_type: str = None
    description: str = None


class ParameterOrderChange(BaseModel):
    param_1: int
    param_2: int


ParameterIn_Pydantic = pydantic_model_creator(Parameter, exclude=("product",))
