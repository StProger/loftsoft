import os

import aiofiles
from fastapi import HTTPException, UploadFile

from axegaoshop.services.utils import random_string
from axegaoshop.settings import ALLOWED_UPLOAD_TYPES, settings


async def handle_upload(file: UploadFile) -> str:
    """
    обработка загрузки на сайт (принимаются только:
     - Изображения
     - Текстовые файлы

     :return:
       file_name (str) - Имя файла и по совместительству идентификатор для получения файла
       по гейту /api/upload/{uid}
    """
    _, ext = os.path.splitext(file.filename)

    img_dir: str = settings.storage_folder_uploads

    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    content: bytes = await file.read()

    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            status_code=406, detail="Only .jpeg or .png or .txt or .svd files allowed"
        )

    file_name = random_string(16) + ext

    async with aiofiles.open(os.path.join(img_dir, file_name), mode="wb") as f:
        await f.write(content)

    return file_name
