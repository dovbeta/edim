import os

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from context_manager import ContextManager
from db.session import AsyncSessionLocal
from gateway.chat_gateway import ChatGateway
from llm_client import GeminiClient
from orchestrator import Orchestrator
from core.chat_request import ChatRequest
from core.contact_request import ContactRequest
from chat_history.repository import ChatHistoryRepository
from chat_history.service import ChatHistoryService

app = FastAPI(title="E-Dim Copilot API")

# -------------------------------------------------
# DEPENDENCIES
# -------------------------------------------------

def get_session_factory():
    return AsyncSessionLocal


# 🧠 Mongo Chat History
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
mongo_db = mongo_client[os.getenv("MONGO_DB", "edim")]
mongo_messages = mongo_db["messages"]

chat_history_repo = ChatHistoryRepository(mongo_messages)
chat_history = ChatHistoryService(chat_history_repo)
llm_client = GeminiClient()
context_manager = ContextManager()


# 🤖 Orchestrator
orchestrator = Orchestrator(
    llm=llm_client,
    context_manager=context_manager,
    chat_history=chat_history
)


# 🚪 Gateway
gateway = ChatGateway(
    session_factory=get_session_factory(),
    orchestrator=orchestrator,
)


# -------------------------------------------------
# ROUTES
# -------------------------------------------------

@app.post("/chat")
async def chat(req: ChatRequest):
    return await gateway.handle_message(
        channel=req.channel,
        external_user_id=req.external_user_id,
        message=req.message,
        first_name=req.first_name,
        last_name=req.last_name,
        username=req.username,
    )


@app.post("/chat/contact")
async def contact(req: ContactRequest):
    return await gateway.handle_contact(
        channel=req.channel,
        external_user_id=req.external_user_id,
        phone=req.phone,
        first_name=req.first_name,
        last_name=req.last_name,
        username=req.username,
    )