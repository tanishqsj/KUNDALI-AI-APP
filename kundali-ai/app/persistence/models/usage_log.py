# Placeholder for kundali-ai/app/persistence/models/usage_log.py
import uuid

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime   

from app.persistence.base import Base


class UsageLog(Base):
    """
    Records a single usage event.

    Used for:
    - quota enforcement
    - billing
    - analytics
    """

    __tablename__ = "usage_logs"

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
    # Usage Details
    # ─────────────────────────────────────────────

    feature: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Feature identifier (ask_llm, voice_astrology, pdf_report, etc.)"
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        doc="Units consumed (usually 1, can be >1 for tokens, minutes, etc.)"
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
        backref="usage_logs",
        lazy="selectin"
    )

    __table_args__ = (
        Index(
            "ix_usage_logs_user_feature_time",
            "user_id",
            "feature",
            "created_at"
        ),
    )
