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


class User(Base):
    __tablename__ = "users"

    # Required fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String(255))

    # Optional fields
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    occupation_grade: Mapped[Optional[OccupationGrades]] = mapped_column(SQLEnum(OccupationGrades), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # relationships
    posts: Mapped[List["Post"]] = relationship(back_populates="author")

    # Required fields with defaults
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[Roles] = mapped_column(SQLEnum(Roles), default=Roles.USER)


