class ChatHistoryService:
    def __init__(self, repo):
        self.repo = repo

    async def save_user_message(
        self,
        user_id: int,
        channel: str,
        text: str,
    ):
        await self.repo.add_message(
            user_id=user_id,
            channel=channel,
            role="user",
            text=text,
        )

    async def save_assistant_message(
        self,
        user_id: int,
        channel: str,
        text: str,
        intent: str | None = None,
    ):
        await self.repo.add_message(
            user_id=user_id,
            channel=channel,
            role="assistant",
            text=text,
            intent=intent,
        )

    async def get_context_messages(
        self,
        user_id: int,
        channel: str,
        limit: int = 1,
        minutes: int = 60,
    ):
        items = await self.repo.get_recent(
            user_id=user_id,
            channel=channel,
            limit=limit,
            minutes=minutes,
        )

        return [
            {"role": m["role"], "content": m["text"]}
            for m in items
        ]