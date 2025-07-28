from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from enum import StrEnum
from datetime import datetime



class PostStatus(StrEnum):
    DRAFT = 'draft'
    PUBLIC = 'public'
    ARCHIVED = 'archived'


class AuthorField(BaseModel):
    author_id: int = Field(...)


class PostCreateInitial(BaseModel):
    title: str
    content: str

class PostCreateFinal(PostCreateInitial, AuthorField):
    pass

class PostRead(BaseModel):
    id: int
    author_id: int
    title: str
    content: str
    rating: int
    created_at: datetime
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    view_count: Optional[int] = None
    status: PostStatus

    class Config:
        from_attributes = True

class PostUpdateInitial(BaseModel):
    id: int
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None

class PostUpdateFinal(PostUpdateInitial, AuthorField):
    pass


class PostDeleteInitial(BaseModel):
    id: int = Field(...)

class PostDeleteFinal(PostDeleteInitial, AuthorField):
    pass


class RatePostInitial(BaseModel):
    post_id: int = Field(...)
    value: Literal[-1, 1] = Field(..., description="-1 is a downvote, 1 is an upvote")

class RatePostFinal(RatePostInitial, AuthorField):
    pass


class DeletePostRatingInitial(BaseModel):
    post_id: int = Field(...)

class DeletePostRatingFinal(DeletePostRatingInitial, AuthorField):
    pass