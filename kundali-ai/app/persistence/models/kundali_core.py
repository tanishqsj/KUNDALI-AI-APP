# Placeholder for kundali-ai/app/persistence/models/kundali_core.py
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
from app.domain.kundali.schemas import KundaliChart, Ascendant, PlanetPosition


class KundaliCore(Base):
    """
    Stores the core D1 (Rashi) kundali.

    This table contains the *calculated astronomical output*
    derived from a BirthProfile.

    It is IMMUTABLE.
    """

    __tablename__ = "kundali_core"

    # ─────────────────────────────────────────────
    # Primary Key
    # ─────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ─────────────────────────────────────────────
    # Ownership / Source
    # ─────────────────────────────────────────────

    birth_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─────────────────────────────────────────────
    # Core Kundali Data (IMMUTABLE)
    # ─────────────────────────────────────────────

    ascendant: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Ascendant sign, degree, nakshatra"
    )

    planets: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Planetary positions with sign, degree, house, nakshatra"
    )

    houses: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="House to sign mapping (1–12)"
    )

    ayanamsa: Mapped[str] = mapped_column(
        nullable=False,
        doc="Ayanamsa used (e.g. Lahiri)"
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

    birth_profile = relationship(
        "BirthProfile",
        backref="kundali_core",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "birth_profile_id",
            name="uq_kundali_core_birth_profile"
        ),
    )

    def to_domain(self) -> KundaliChart:
        """
        Convert the SQLAlchemy model to the domain KundaliChart.
        """
        return KundaliChart(
            ascendant=Ascendant(**self.ascendant),
                planets={k: PlanetPosition(name=k, **v) for k, v in self.planets.items()},
            houses=self.houses,
            ayanamsa=self.ayanamsa,
        )
    def to_dict(self) -> dict:
        """
        Convert the model to a dictionary for serialization.
        """
        return {
            "id": str(self.id),
            "birth_profile_id": str(self.birth_profile_id),
            "ascendant": self.ascendant,
            "planets": self.planets,
            "houses": self.houses,
            "ayanamsa": self.ayanamsa,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }