import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.persistence.base import Base


class Subscription(Base):
    """
    Represents a subscription plan for a user.

    Subscriptions are time-bound and historical.
    Only ONE subscription should be active at a time.
    """

    __tablename__ = "subscriptions"

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
    # Plan Details
    # ─────────────────────────────────────────────

    plan_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="free, pro, premium, enterprise"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # ─────────────────────────────────────────────
    # Validity Window
    # ─────────────────────────────────────────────

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
        backref="subscriptions",
        lazy="selectin"
    )

    __table_args__ = (
        Index(
            "ix_subscriptions_user_active",
            "user_id",
            "is_active"
        ),
    )
