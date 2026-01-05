import uuid
from datetime import date, time, datetime

from sqlalchemy import (
    Date,
    Time,
    String,
    Float,
    ForeignKey,
    DateTime,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.persistence.base import Base


class BirthProfile(Base):
    """
    Stores immutable birth details for kundali calculation.

    This table represents the *input truth*.
    All astrology is derived from this data.
    """

    __tablename__ = "birth_profiles"

    # ─────────────────────────────────────────────
    # Primary Key
    # ─────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ─────────────────────────────────────────────
    # Ownership
    # ─────────────────────────────────────────────

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # ─────────────────────────────────────────────
    # Identity (for display only)
    # ─────────────────────────────────────────────

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # ─────────────────────────────────────────────
    # Birth Details (IMMUTABLE)
    # ─────────────────────────────────────────────

    birth_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    birth_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    birth_place: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # ─────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # ─────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────

    user = relationship(
        "User",
        backref="birth_profiles",
        lazy="selectin"
    )

    __table_args__ = (
        Index(
            "ix_birth_profiles_lat_lon",
            "latitude",
            "longitude"
        ),
    )
