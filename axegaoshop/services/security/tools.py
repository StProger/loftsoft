import time
from datetime import datetime, timedelta
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from axegaoshop.settings import settings

ACCESS_TOKEN_EXPIRE_MINUTES: int = 66000
REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

ALGORITHM: str = "HS256"

password_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password: str) -> str:
    """хеширование пароля"""
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    """совпадают ли введенный пароль с хешированным"""
    return password_context.verify(password, hashed_pass)


def create_access_token(
    subject: Union[str, Any], expires_delta: int | None = None
) -> str:
    """создание JWT токена"""
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta

    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, ALGORITHM)

    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    """создание refresh токеан (не используется)"""
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_refresh_secret_key, ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str) -> dict:
    """получение данных из jwn токена"""
    try:
        decoded_token: dict = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[ALGORITHM]
        )

        return decoded_token if decoded_token["exp"] >= time.time() else None
    except:
        return {}


def generate_password_drop_link(uid: str):
    """генерация ссылки для сброса пароля, которая передается в письме на почту"""
    return f"/user/password/reset/{uid}"
