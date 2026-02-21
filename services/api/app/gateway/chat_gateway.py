import re
from sqlalchemy import select

from db.models import ChatIdentity, User


class ChatGateway:

    def __init__(self, session_factory, orchestrator):
        self.session_factory = session_factory
        self.orchestrator = orchestrator

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

            identity = await self._get_identity(
                session, channel, external_user_id
            )

            # 🆕 новий користувач
            if not identity:
                identity = ChatIdentity(
                    channel=channel,
                    external_id=external_user_id,
                    verified=False,
                )
                session.add(identity)
                await session.commit()

                return {
                    "need_phone": True,
                    "text": (
                        "👋 Вітаємо!\n\n"
                        "Поділіться номером телефону 📱\n"
                        "Можливо ми знайдемо вашу квартиру."
                    ),
                }

            # 📱 identity є але не привʼязаний або не verified
            if not identity.user_id or not identity.verified:
                return {
                    "need_phone": True,
                    "text": "Будь ласка, поділіться номером телефону 📱",
                }

            # ✅ нормальний сценарій
            answer = await self.orchestrator.handle(
                message=message,
                user_id=identity.user_id,
                channel=channel,
            )

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

            identity = await self._get_identity(
                session, channel, external_user_id
            )

            if not identity:
                identity = ChatIdentity(
                    channel=channel,
                    external_id=external_user_id,
                    verified=False,
                )
                session.add(identity)

            # 📱 нормалізація телефону
            phone_norm = self._normalize_phone(phone)
            identity.phone = phone_norm

            # 🔎 пошук користувача
            user = await self._find_user_by_phone(session, phone_norm)

            if user:
                identity.user_id = user.id
                identity.verified = True

                await session.commit()

                return {
                    "text": (
                        f"Дякуємо, {user.first_name or ''}! 🙌\n"
                        "Ми знайшли вас у системі ОСББ."
                    )
                }

            # не знайдено
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