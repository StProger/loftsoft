from pydantic import BaseModel


class UploadOut(BaseModel):
    upload: str
