import typing

from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from axegaoshop.db.models.ticket import Ticket, TicketMessage, TicketMessageAttachment


class TicketMessageSend(BaseModel):
    id: typing.Optional[int] = None
    text: str
    attachments: list[str] = []


TicketIn_Pydantic = pydantic_model_creator(Ticket)
