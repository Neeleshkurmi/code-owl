from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id"),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    file: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    line: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    suggestion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    review: Mapped["Review"] = relationship(
        back_populates="findings",
    )