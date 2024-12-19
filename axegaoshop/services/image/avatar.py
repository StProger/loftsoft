import os

from avatar_generator import Avatar

from axegaoshop.services.utils import random_string
from axegaoshop.settings import settings


def create_user_photo(username: str) -> str:
    """генерация аватарки пользователя стандартной (первая буква логина)"""
    avatar = Avatar().generate(200, string=username, filetype="PNG")

    file_uid = f"{random_string()}.png"
    file_path = os.path.join(settings.storage_folder_uploads, file_uid)

    with open(file_path, "wb") as f:
        f.write(avatar)

    return file_uid
