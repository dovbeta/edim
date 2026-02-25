import re
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from uuid import uuid4

from db.models import ChatIdentity, User



class ChatGateway:

    def __init__(self, session_factory, orchestrator, failure_logger=None):
        self.session_factory = session_factory
        self.orchestrator = orchestrator
        self.failure_logger = failure_logger

    # =====================================================
    # TEXT MESSAGE
    # =====================================================

    async def handle_message(
            self,
            channel: str,
            external_user_id: str,
            message: str,
            first_name: str | None = None,
            last_name: str | None = None,
            username: str | None = None,
    ):
        async with self.session_factory() as session:

            identity = await self._get_or_create_identity(
                session, channel, external_user_id
            )

            # 🆕 новий або без телефону
            if not identity.phone:
                return {
                    "need_phone": True,
                    "text": (
                        "👋 Вітаємо!\n\n"
                        "Поділіться номером телефону 📱\n"
                        "Можливо ми знайдемо інформацію про вашу нерухомість."
                    ),
                }

            # користувач не знайдений
            if not identity.user_id:
                return {
                    "text": (
                        "👋 Вітаємо!\n\n"
                        "Зверніться до адміністратора системи"
                    ),
                }

            try:
                answer = await self.orchestrator.handle(
                    message=message,
                    user_id=identity.user_id,
                    channel=channel,
                )
            except Exception as e:
                if self.failure_logger:
                    await self.failure_logger.log_failure(
                        component="chat_gateway_handle_message",
                        exception=e,
                        meta={
                            "user_id": str(identity.user_id),
                            "channel": channel,
                            "external_user_id": external_user_id,
                        }
                    )
                return {"text": "⚠️ Вибачте, сталася внутрішня помилка. Спробуйте пізніше."}

            return {"text": answer}

    # =====================================================
    # CONTACT
    # =====================================================

    async def handle_contact(
            self,
            channel: str,
            external_user_id: str,
            phone: str,
            first_name: str | None = None,
            last_name: str | None = None,
            username: str | None = None,
    ):
        async with self.session_factory() as session:
            identity = await self._get_or_create_identity(
                session, channel, external_user_id
            )

            phone_norm = self._normalize_phone(phone)
            identity.phone = phone_norm

            user = await self._find_user_by_phone(session, phone_norm)

            if user:
                identity.user_id = user.id
                identity.verified = True
                await session.commit()

                return {
                    "text": (
                        f"Дякуємо, {user.first_name or ''}! 🙌\n"
                        "Ми знайшли вас у системі."
                    )
                }

            identity.verified = False
            await session.commit()

            return {
                "text": (
                    "Дякуємо! 📱\n"
                    "Ми не знайшли вас у системі ОСББ.\n"
                    "Адміністратор звʼяжеться з вами."
                )
            }

    # =====================================================
    # HELPERS
    # =====================================================

    async def _get_identity(self, session, channel, external_id):
        q = select(ChatIdentity).where(
            ChatIdentity.channel == channel,
            ChatIdentity.external_id == external_id,
        )
        res = await session.execute(q)
        return res.scalar_one_or_none()

    async def _find_user_by_phone(self, session, phone):
        q = select(User).where(User.phone == phone)
        res = await session.execute(q)
        return res.scalar_one_or_none()

    # =====================================================
    # PHONE NORMALIZATION (UA)
    # =====================================================

    def _normalize_phone(self, phone: str) -> str:
        digits = re.sub(r"\D", "", phone)

        if digits.startswith("0"):
            digits = "38" + digits

        if not digits.startswith("38"):
            digits = "38" + digits

        return "+" + digits

    async def _get_or_create_identity(self, session, channel, external_id):
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
            # новий створений
            identity_id = row[0]
        else:
            # вже існує
            q = select(ChatIdentity.id).where(
                ChatIdentity.channel == channel,
                ChatIdentity.external_id == external_id,
            )
            identity_id = (await session.execute(q)).scalar_one()

        # дістаємо ORM-об’єкт
        q = select(ChatIdentity).where(ChatIdentity.id == identity_id)
        return (await session.execute(q)).scalar_one()