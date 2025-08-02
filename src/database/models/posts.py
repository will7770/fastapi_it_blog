from ..core import Base
from datetime import datetime
from enum import Enum, StrEnum
from typing import Optional, List, Annotated
from sqlalchemy import (Uuid, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, func, Enum as SQLEnum,
                        LargeBinary, Integer)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from src.database.models.users import bookmark_table
from src.database.models.tags import tags_to_posts



created_at = Annotated[
    datetime,
    mapped_column(
        DateTime,
        server_default=func.now(),
        init=False
    )
]

updated_at = Annotated[
    datetime,
    mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        init=False
    )
]

class PostStatus(StrEnum):
    DRAFT = 'draft'
    PUBLIC = 'public'
    ARCHIVED = 'archived'

class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    tags: Mapped[list["Tags"]] = relationship(
        secondary=tags_to_posts,
        back_populates="post_tags",
        lazy='joined'
    )
    bookmarked_by: Mapped[list["User"]] = relationship(
        secondary=bookmark_table,
        back_populates="bookmarks",
        lazy='raise'
    )
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", lazy='joined')
    author: Mapped["User"] = relationship(back_populates="posts")
    votes: Mapped["Vote"] = relationship(back_populates="post")

    rating: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PostStatus] = mapped_column(SQLEnum(PostStatus), default=PostStatus.DRAFT)

    def __repr__(self):
        return f"Id: {self.id} | Author: {self.author_id} | Title: {self.title}"


class Vote(Base):
    __tablename__ = 'votes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    value: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship(back_populates="votes")
    post: Mapped["Post"] = relationship(back_populates="votes")

    __table_args__ = (
        UniqueConstraint('author_id', 'post_id', name='_user_post_uc'),
    )