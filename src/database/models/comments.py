from ..core import Base
from datetime import datetime
from enum import Enum, StrEnum
from typing import Optional, List, Annotated
from sqlalchemy import Uuid, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, func, Enum as SQLEnum, LargeBinary, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB



created_at = Annotated[
    datetime,
    mapped_column(
        DateTime,
        server_default=func.now(),
        init=False
    )
]

class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[created_at]

    author: Mapped["User"] = relationship(back_populates="comments")
    post: Mapped["Post"] = relationship(back_populates="comments")
    parent: Mapped["Comment"] = relationship(
        remote_side=[id],
        back_populates="replies"
    )
    replies: Mapped[List["Comment"]] = relationship(
        back_populates="parent",
        order_by="Comment.created_at.asc()"
    )

    @property
    def has_available_parent(self):
        return True if self.parent_id else False