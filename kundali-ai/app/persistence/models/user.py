import uuid
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime

from app.persistence.base import Base


class User(Base):
    """
    Represents a system user.

    This can be:
    - a public user
    - an admin user
    - a future API / enterprise user

    Astrology data is NOT stored here.
    """

    __tablename__ = "users"

    # ─────────────────────────────────────────────
    # Primary Key
    # ─────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ─────────────────────────────────────────────
    # Identity
    # ─────────────────────────────────────────────

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    # ─────────────────────────────────────────────
    # Role & Status
    # ─────────────────────────────────────────────

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # ─────────────────────────────────────────────
    # Timestamps
    # ─────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
