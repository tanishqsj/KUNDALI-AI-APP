import uuid
from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.persistence.base import Base


class RuleMapping(Base):
    """
    Records why a rule matched for a specific kundali.

    This enables full explainability:
    - Which rule fired
    - Which kundali it applied to
    - What exact entity caused the match
    """

    __tablename__ = "rule_mappings"

    # ─────────────────────────────────────────────
    # Primary Key
    # ─────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ─────────────────────────────────────────────
    # References
    # ─────────────────────────────────────────────

    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    kundali_core_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kundali_core.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─────────────────────────────────────────────
    # Triggering Entity
    # ─────────────────────────────────────────────

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="planet, house, dosha, yoga, transit, etc."
    )

    entity_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Identifier like 'Jupiter', '10th_house', 'MangalDosha'"
    )

    entity_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Snapshot of the kundali data that caused the match"
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

    rule = relationship(
        "Rule",
        lazy="selectin"
    )

    kundali_core = relationship(
        "KundaliCore",
        lazy="selectin"
    )

    __table_args__ = (
        Index(
            "ix_rule_mappings_entity",
            "entity_type",
            "entity_key"
        ),
    )
