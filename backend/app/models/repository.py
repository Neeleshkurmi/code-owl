from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class Repository(Base) :
    __tablename__ = "repositories"

    id : Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    github_repo_id : Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )

    name : Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name : Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    owner : Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    url : Mapped[str] = mapped_column(
        String(511),
        default=True,
        nullable=False
    )

    is_active : Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    pull_requests : Mapped[list["PullRequest"]] = relationship(
        back_populates="repository",
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

