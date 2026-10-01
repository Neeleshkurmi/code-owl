from datetime import datetime
from turtle import back

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ReviewRun(Base) :
    __tablename__ = "review_runs"

    __table_args__ = (
        UniqueConstraint(
            "pull_request_id",
            "commit_sha",
            name= "uq_review_runs_pull_request_commit",
        ),
    )

    id : Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    pull_request_id : Mapped[int] = mapped_column(
        ForeignKey("pull_requests.id"),
        nullable=False,
    )

    status : Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    commit_sha : Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    started_at : Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at : Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    error_message : Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    pull_request : Mapped["PullRequest"] = relationship(
        back_populates="review_runs",
    )

    reviews : Mapped[list["Review"]] = relationship(
        back_populates="review_run",
        cascade="all, delete-orphan",
    )