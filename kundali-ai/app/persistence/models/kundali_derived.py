import uuid
from sqlalchemy import (
    ForeignKey,
    DateTime,
    JSON,
    UniqueConstraint,
)
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.persistence.base import Base


class KundaliDerived(Base):
    """
    Stores derived astrology from a KundaliCore.

    This includes:
    - Doshas
    - Yogas
    - Strengths of planets and houses
    - High-level summaries

    This data is RECOMPUTABLE and VERSIONABLE.
    """

    __tablename__ = "kundali_derived"

    # ─────────────────────────────────────────────
    # Primary Key
    # ─────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ─────────────────────────────────────────────
    # Source
    # ─────────────────────────────────────────────

    kundali_core_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kundali_core.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─────────────────────────────────────────────
    # Derived Data
    # ─────────────────────────────────────────────

    doshas: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Doshas like Mangal, Kaal Sarp, etc."
    )

    yogas: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Detected yogas and combinations"
    )

    planet_strengths: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Planetary strengths"
    )

    house_strengths: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="House strengths"
    )

    summary: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="High-level astrological summary"
    )

    # ─────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────

    calculation_version: Mapped[str] = mapped_column(
        nullable=False,
        doc="Version of derived logic used"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # ─────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────

    kundali_core = relationship(
        "KundaliCore",
        backref="derived",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "kundali_core_id",
            "calculation_version",
            name="uq_kundali_derived_version"
        ),
    )

    def to_dict(self) -> dict:
        """
        Convert the model to a dictionary for serialization.
        """
        return {
            "id": str(self.id),
            "kundali_core_id": str(self.kundali_core_id),
            "doshas": self.doshas,
            "yogas": self.yogas,
            "planet_strengths": self.planet_strengths,
            "house_strengths": self.house_strengths,
            "calculation_version": self.calculation_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
