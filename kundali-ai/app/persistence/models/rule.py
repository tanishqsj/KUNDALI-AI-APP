import uuid
from sqlalchemy import (
    String,
    Boolean,
    Integer,
    JSON,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime

from app.persistence.base import Base


class Rule(Base):
    """
    Represents a single astrology rule.

    Rules are:
    - versioned
    - data-driven
    - evaluated by the rule engine
    """

    __tablename__ = "rules"

    # ─────────────────────────────────────────────
    # Primary Key
    # ─────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ─────────────────────────────────────────────
    # Rule Identity
    # ─────────────────────────────────────────────

    rule_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Stable identifier for the rule (e.g. career_strong_jupiter)"
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="career, marriage, health, timing, etc."
    )

    # ─────────────────────────────────────────────
    # Rule Definition
    # ─────────────────────────────────────────────

    conditions: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Structured conditions evaluated by rule engine"
    )

    effects: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Structured effects used by explanation & AI"
    )

    # ─────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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

    __table_args__ = (
        UniqueConstraint(
            "rule_key",
            "version",
            name="uq_rule_key_version"
        ),
    )
