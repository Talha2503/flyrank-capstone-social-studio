from pydantic import BaseModel
from typing import Optional


class PostCreate(BaseModel):
    source_type: str          # "url" or "markdown"
    source_content: str


class PostOut(BaseModel):
    id: str
    source_type: str
    body: str

    class Config:
        from_attributes = True


class VariantGenerateRequest(BaseModel):
    platforms: list[str]


class VariantOut(BaseModel):
    id: str
    post_id: str
    platform: str
    content: str
    status: str

    class Config:
        from_attributes = True