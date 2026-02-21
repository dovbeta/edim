from datetime import datetime, timedelta
from typing import List, Dict, Any


class ChatHistoryRepository:
    def __init__(self, collection):
        self.col = collection

    async def add_message(
        self,
        user_id,
        channel: str,
        role: str,
        text: str,
        intent: str | None = None,
        meta: dict | None = None,
    ):
        doc = {
            "user_id": str(user_id),  # ✅ UUID → str
            "channel": channel,
            "role": role,
            "text": text,
            "intent": intent,
            "meta": meta or {},
            "created_at": datetime.utcnow(),
        }
        await self.col.insert_one(doc)

    async def get_recent(
        self,
        user_id,
        channel: str,
        limit: int = 10,
        minutes: int = 60,
    ) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - timedelta(minutes=minutes)

        cursor = (
            self.col.find(
                {
                    "user_id": str(user_id),  # ✅ UUID → str
                    "channel": channel,
                    "created_at": {"$gte": since},
                }
            )
            .sort("created_at", -1)
            .limit(limit)
        )

        items = await cursor.to_list(length=limit)
        items.reverse()
        return items