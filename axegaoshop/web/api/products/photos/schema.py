import typing

from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.product import ProductPhoto


class PhotoCreate(BaseModel):
    photo: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "photo": "grfwefwrgre.jpg",
                },
                {
                    "photo": "qlmzvywrge.jpg",
                },
            ]
        }
    }


class PhotoUpdate(BaseModel):
    photo: str
    main: typing.Optional[bool] = None


PhotoIn_Pydantic = pydantic_model_creator(ProductPhoto, exclude=("product",))
