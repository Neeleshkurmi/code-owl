from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    pull_request_id: Mapped[int] = mapped_column(
        ForeignKey("pull_requests.id"),
        nullable=False,
    )

    review_run_id : Mapped[int] = mapped_column(
        ForeignKey("review_runs.id"),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    pull_request: Mapped["PullRequest"] = relationship(
        back_populates="reviews",
    )

    review_run : Mapped["ReviewRun"] = relationship(
        back_populates="reviews",
    )

    findings: Mapped[list["ReviewFinding"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )