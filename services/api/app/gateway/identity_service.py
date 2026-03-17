import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from db.models import ChatIdentity, User


class IdentityService:
    """Encapsulates chat identity and user lookup logic."""

    async def get_or_create_identity(self, session, channel: str, external_id: str) -> ChatIdentity:
        stmt = (
            insert(ChatIdentity)
            .values(
                id=uuid4(),
                channel=channel,
                external_id=external_id,
                verified=False,
            )
            .on_conflict_do_nothing(
                index_elements=["channel", "external_id"]
            )
            .returning(ChatIdentity.id)
        )

        res = await session.execute(stmt)
        row = res.first()

        if row:
            identity_id = row[0]
        else:
            q = select(ChatIdentity.id).where(
                ChatIdentity.channel == channel,
                ChatIdentity.external_id == external_id,
            )
            identity_id = (await session.execute(q)).scalar_one()

        q = select(ChatIdentity).where(ChatIdentity.id == identity_id)
        return (await session.execute(q)).scalar_one()

    async def find_user_by_phone(self, session, phone: str) -> User | None:
        q = select(User).where(User.phone == phone)
        res = await session.execute(q)
        return res.scalar_one_or_none()

    def normalize_phone(self, phone: str) -> str:
        """UA-specific phone normalization to +38XXXXXXXXXX."""
        digits = re.sub(r"\D", "", phone)

        if digits.startswith("0"):
            digits = "38" + digits

        if not digits.startswith("38"):
            digits = "38" + digits

        return "+" + digits

