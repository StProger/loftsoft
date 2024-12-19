from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.faq import Faq


class FaqPydanticDb(BaseModel):
    id: int
    content: str
    title: str


class FaqPydanticUser(BaseModel):
    content: str
    title: str


class FaqPydanticAdmin(BaseModel):
    id: int
    content: str
    title: str


class FaqPydanticAdminCreate(BaseModel):
    content: str
    title: str


Faqs_Pydantic = pydantic_model_creator(Faq)
