from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.partner import Partner


class CreatePartner(BaseModel):
    photo: str


PartnerIn_Pydantic = pydantic_model_creator(Partner)
