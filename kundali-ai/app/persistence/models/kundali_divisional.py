import uuid
from sqlalchemy import (
    ForeignKey,
    DateTime,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.persistence.base import Base


class KundaliDivisional(Base):
    """
    Stores divisional charts derived from KundaliCore.

    Examples:
    - D9 (Navamsha)
    - D10 (Dashamsha)
    - Future: D7, D12, D60

    These charts are STRUCTURAL, not interpretive.
    """

    __tablename__ = "kundali_divisional"

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
    # Divisional Metadata
    # ─────────────────────────────────────────────

    chart_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Divisional chart type (D9, D10, etc.)"
    )

    chart_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Planetary placements and ascendant for this divisional chart"
    )

    calculation_version: Mapped[str] = mapped_column(
        nullable=False,
        doc="Version of divisional calculation logic"
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

    kundali_core = relationship(
        "KundaliCore",
        backref="divisionals",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "kundali_core_id",
            "chart_type",
            "calculation_version",
            name="uq_kundali_divisional_chart"
        ),
    )
