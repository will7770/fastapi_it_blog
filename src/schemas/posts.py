from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import StrEnum
from datetime import datetime



class PostStatus(StrEnum):
    DRAFT = 'draft'
    PUBLIC = 'public'
    ARCHIVED = 'archived'


class PostCreateInitial(BaseModel):
    title: str
    content: str

class PostCreateFinal(PostCreateInitial):
    author_id: int = Field(...)


class PostRead(BaseModel):
    id: int
    author_id: int
    title: str
    content: str
    created_at: datetime
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    view_count: Optional[int] = None
    status: PostStatus

    class Config:
        from_attributes = True

class PostUpdate(BaseModel):
    id: int
    author_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None