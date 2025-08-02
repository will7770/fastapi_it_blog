from ..core import Base
from datetime import datetime
from enum import Enum, StrEnum
from typing import Optional, List, Annotated
from sqlalchemy import (Uuid, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint,
                        Index, func, Enum as SQLEnum, LargeBinary, Integer, Table, Column)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB



tags_to_users = Table(
    "tags_to_users",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)


tags_to_posts = Table(
    "tags_to_posts",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)


class Tags(Base):
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    favorited_by: Mapped[list["User"]] = relationship(back_populates="favorite_tags", secondary=tags_to_users)
    post_tags: Mapped[list["Post"]] = relationship(back_populates="tags", secondary=tags_to_posts)

    def __repr__(self):
        return f"Id: {self.id} | Name: {self.name}"