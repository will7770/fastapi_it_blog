from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from enum import StrEnum
from datetime import datetime


class AuthorField(BaseModel):
    author_id: int = Field(...)


class CommentRead(AuthorField):
    id: int
    content: str
    post_id: int
    parent_id: Optional[int]

    class Config:
        from_attributes = True


class CreateCommentInitial(BaseModel):
    content: str
    post_id: int
    parent_id: int | None = None

class CreateCommentFinal(CreateCommentInitial, AuthorField):
    pass


class DeleteCommentInitial(BaseModel):
    comment_id: int

class DeleteCommentFinal(DeleteCommentInitial, AuthorField):
    pass