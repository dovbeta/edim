import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class ChatIdentity(Base):
    __tablename__ = "chat_identities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    external_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[Optional["User"]] = relationship(
        back_populates="chat_identities"
    )

    __table_args__ = (
        UniqueConstraint(
            "channel",
            "external_id",
            name="uq_chat_identity_channel_external",
        ),
        Index("idx_chat_identity_user", "user_id"),
    )
