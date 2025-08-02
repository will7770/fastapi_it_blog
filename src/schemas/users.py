from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import StrEnum
from datetime import datetime
from .posts import PostRead, Tag



class Roles(StrEnum):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'


class OccupationGrades(StrEnum):
    TRAINEE = 'trainee'
    JUNIOR = 'junior'
    MIDDLE = 'middle'
    SENIOR = 'senior'
    LEAD = 'lead'


class UserCreate(BaseModel):
    username: str = Field(..., min_length=4, max_length=25)
    email: EmailStr
    password: str = Field(...)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str = Field(..., min_length=4, max_length=25)

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    occupation_grade: Optional[OccupationGrades] = None
    last_login: Optional[datetime] = None

    created_at: datetime
    is_verified: bool
    role: Roles


    class Config:
        from_attributes = True


class Profile(UserRead):
    bookmarks: list[PostRead] = []
    favorite_tags: list[Tag] = []


class UserUpdateInitial(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    occupation_grade: Optional[OccupationGrades] = None

class UserUpdateFinal(UserUpdateInitial):
    id: int = Field(...)


class UserDelete(BaseModel):
    id: int = Field(...)
    password: str = Field(...)