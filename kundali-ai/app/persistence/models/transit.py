import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.persistence.base import Base


class Transit(Base):
    """
    Stores planetary transits for a specific date.

    This data is GLOBAL (same for all users)
    and is used for gochar & timing calculations.
    """

    __tablename__ = "transits"

    # ─────────────────────────────────────────────
    # Primary Key
    # ─────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ─────────────────────────────────────────────
    # Transit Date (GLOBAL KEY)
    # ─────────────────────────────────────────────

    transit_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date for which this transit applies"
    )

    # ─────────────────────────────────────────────
    # Transit Data
    # ─────────────────────────────────────────────

    planets: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Planetary positions, retrograde flags, degrees"
    )

    ayanamsa: Mapped[str] = mapped_column(
        nullable=False,
        doc="Ayanamsa used for this transit"
    )

    # ─────────────────────────────────────────────
    # Metadata
    # ─────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "transit_date",
            "ayanamsa",
            name="uq_transit_date_ayanamsa"
        ),
    )
