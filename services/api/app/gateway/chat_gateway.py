from gateway.identity_service import IdentityService


class ChatGateway:

    def __init__(self, session_factory, orchestrator, failure_logger=None, identity_service: IdentityService | None = None):
        self.session_factory = session_factory
        self.orchestrator = orchestrator
        self.failure_logger = failure_logger
        self.identity_service = identity_service or IdentityService()

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

            identity = await self.identity_service.get_or_create_identity(
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
            identity = await self.identity_service.get_or_create_identity(
                session, channel, external_user_id
            )

            phone_norm = self.identity_service.normalize_phone(phone)
            identity.phone = phone_norm

            user = await self.identity_service.find_user_by_phone(session, phone_norm)

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

    # Ідентифікація та робота з телефоном винесені в IdentityService