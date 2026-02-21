from motor.motor_asyncio import AsyncIOMotorClient

from repository import ChatHistoryRepository
from service import ChatHistoryService


def create_chat_history_service(mongo_url: str, db_name: str):
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    col = db["messages"]

    repo = ChatHistoryRepository(col)
    return ChatHistoryService(repo)