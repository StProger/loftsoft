import typing

from pydantic import BaseModel, model_validator


class ItemRequest(BaseModel):
    contact_type: typing.Literal["email", "whatsapp", "telegram"]
    contact: str
    files: typing.Optional[list[str]] = None
    count: typing.Optional[int] = None
    full_name: typing.Optional[str] = None
    description: typing.Optional[str] = None

    @model_validator(mode="after")
    def validate_item_request(self) -> "ItemRequest":
        if not self.files and (
            not self.count or not self.full_name or not self.description
        ):
            raise ValueError("Provide count, full_name ad description!")

        return self
