import os.path

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.responses import FileResponse

from axegaoshop.services.image.helper import handle_upload
from axegaoshop.settings import settings
from axegaoshop.web.api.uploads.schema import UploadOut

router = APIRouter(tags=["Uploads"])


@router.post("/upload", response_model=UploadOut)
async def create_upload(file: UploadFile = File()):
    data = await handle_upload(file)

    return UploadOut(upload=data)


@router.get("/uploads/{uid}")
async def get_upload(uid: str) -> FileResponse:
    file_: str = settings.storage_folder_uploads + "/" + uid

    if os.path.exists(settings.storage_folder_uploads + "/" + uid):
        return FileResponse(file_, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
