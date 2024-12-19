import typing

from pydantic import BaseModel


class TokenCreated(BaseModel):
    access_token: str
    refresh_token: str

    class Config:
        from_attributes = True


class TokenRequest(BaseModel):
    """request to token in /user/login"""

    email: str
    password: typing.Optional[str] = None
