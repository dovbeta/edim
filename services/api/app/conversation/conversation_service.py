from typing import List, Dict

class ConversationService:
    """
    Responsibilities:
    - store user/assistant messages
    - return recent history window
    - build formatted chat context for LLM
    """
    def __init__(self, repo):
        self.repo = repo

    async def save_user_message(self, user_id: int, text: str, channel: str = "default"):
        """Stores a user message."""
        await self.repo.add_message(
            user_id=user_id,
            channel=channel,
            role="user",
            text=text,
        )

    async def save_ai_message(self, user_id: int, text: str, channel: str = "default"):
        """Stores an assistant message."""
        await self.repo.add_message(
            user_id=user_id,
            channel=channel,
            role="assistant",
            text=text,
        )

    async def get_recent_history(self, user_id: int, limit: int = 10, channel: str = "default") -> List[Dict]:
        """Returns recent history window."""
        items = await self.repo.get_recent(
            user_id=user_id,
            channel=channel,
            limit=limit,
        )
        return [
            {"role": m["role"], "content": m["text"]}
            for m in items
        ]

    async def build_context(self, user_id: int, limit: int = 10, channel: str = "default") -> List[Dict]:
        """Builds formatted chat context for LLM."""
        return await self.get_recent_history(user_id=user_id, limit=limit, channel=channel)
