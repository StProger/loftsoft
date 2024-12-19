from fastapi import Depends, HTTPException
from starlette.requests import Request

from axegaoshop.db.models.token import Token
from axegaoshop.db.models.user import User


async def get_current_user(request: Request) -> User | None:
    """получаем информацию о текущем пользователе по токену"""
    if not request.headers.get("Authorization"):
        return None

    token: str = request.headers.get("Authorization").split()[1]

    token_: Token | None = await Token.get_or_none(access_token=token)

    if not token_:
        raise HTTPException(status_code=404, detail="Not authenticated")

    user: User = await token_.get_user()

    if not user:
        raise HTTPException(status_code=404, detail="Not authenticated")

    if not user.is_active:
        raise HTTPException(status_code=404, detail="INACTIVE")
    return user


async def current_user_is_admin(user: User = Depends(get_current_user)):
    """проверка что пользователь - админ"""
    if not user:
        raise HTTPException(status_code=404, detail="UNAUTHORIZED")

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    return user
