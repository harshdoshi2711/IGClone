# app/schemas/post_schemas.py
from pydantic import BaseModel
from typing import Optional

class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None

class PostRead(PostCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True
