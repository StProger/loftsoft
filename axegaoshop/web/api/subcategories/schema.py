import typing

from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.subcategory import Subcategory


class SubcategoryCreate(BaseModel):
    title: str
    category_id: int


class SubcategoryOrderChange(BaseModel):
    subcategory_1: int
    subcategory_2: int


class SubcategoryUpdate(BaseModel):
    title: typing.Optional[str] = None
    category_id: typing.Optional[int] = None


SubcategoryIn_Pydantic = pydantic_model_creator(Subcategory, exclude=("category",))
