"""
Kundali Match Model

Stores the results of Ashta Koot matching between two Kundalis.
"""

import uuid
from sqlalchemy import (
    ForeignKey,
    DateTime,
    JSON,
    Float,
    Integer,
    String,
)
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.persistence.base import Base


class KundaliMatch(Base):
    """
    Stores Kundali Milan (compatibility matching) results.
    
    References two KundaliCore entries and stores the Ashta Koot score.
    """

    __tablename__ = "kundali_matches"

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

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─────────────────────────────────────────────
    # References to Kundalis
    # ─────────────────────────────────────────────

    boy_kundali_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kundali_core.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    girl_kundali_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kundali_core.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─────────────────────────────────────────────
    # Matching Results
    # ─────────────────────────────────────────────

    total_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Total Ashta Koot score"
    )

    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=36,
        doc="Maximum possible score (36)"
    )

    verdict: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Matching verdict: Excellent/Good/Average/Below Average"
    )

    factors: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Detailed breakdown of all 8 Koot factors"
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
        backref="matches",
        lazy="selectin"
    )

    boy_kundali = relationship(
        "KundaliCore",
        foreign_keys=[boy_kundali_id],
        lazy="selectin"
    )

    girl_kundali = relationship(
        "KundaliCore",
        foreign_keys=[girl_kundali_id],
        lazy="selectin"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "boy_kundali_id": str(self.boy_kundali_id),
            "girl_kundali_id": str(self.girl_kundali_id),
            "total_score": self.total_score,
            "max_score": self.max_score,
            "verdict": self.verdict,
            "factors": self.factors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
