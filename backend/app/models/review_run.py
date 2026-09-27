from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ReviewRun(Base) :
    __tablename__ = "review_runs"

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

    completed_at : Mapped[str | None] = mapped_column(
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