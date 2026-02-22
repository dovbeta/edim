import os

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from db.session import AsyncSessionLocal

# context
from context.context_manager import ContextManager
from context.context_provider import ContextProvider

# chat history
from chat_history.repository import ChatHistoryRepository
from chat_history.service import ChatHistoryService

# llm
from llm.gemini import GeminiClient
from policy.prompt_builder import EDIMPromptBuilder
from planning.plan_logger import PlanLogger

# planning
from planning.planner import Planner

# execution
from execution.sql_validator import SQLValidator
from execution.sql_executor import SQLExecutor
from planning.prompts import PlannerPromptBuilder
from planning.sql_schema import SQL_SCHEMA

# response
from response.responder import Responder

# orchestrator + gateway
from orchestrator.orchestrator import Orchestrator
from gateway.chat_gateway import ChatGateway

# api models
from core.chat_request import ChatRequest
from core.contact_request import ContactRequest


app = FastAPI(title="E-Dim Copilot API")


# -------------------------------------------------
# DB / SESSION
# -------------------------------------------------

def get_session_factory():
    return AsyncSessionLocal


# -------------------------------------------------
# MONGO CHAT HISTORY
# -------------------------------------------------

mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
mongo_db = mongo_client[os.getenv("MONGO_DB", "edim")]
mongo_messages = mongo_db["messages"]

chat_history_repo = ChatHistoryRepository(mongo_messages)
chat_history = ChatHistoryService(chat_history_repo)


# -------------------------------------------------
# LLM
# -------------------------------------------------

llm_client = GeminiClient(
    system_prompt=EDIMPromptBuilder.BASE_SYSTEM
)


# -------------------------------------------------
# CONTEXT
# -------------------------------------------------

context_manager = ContextManager()
context_provider = ContextProvider(context_manager)


# -------------------------------------------------
# PLANNER
# -------------------------------------------------

planner_prompt_builder = PlannerPromptBuilder(schema=SQL_SCHEMA)

planner = Planner(
    llm=llm_client,
    schema=SQL_SCHEMA,
    prompt_builder=planner_prompt_builder,
)
planner_logs = mongo_db["planner_logs"]
plan_logger = PlanLogger(planner_logs)


# -------------------------------------------------
# SQL EXECUTION
# -------------------------------------------------

validator = SQLValidator(
    allowed_tables={
        "users",
        "units",
        "buildings",
        "organizations",
        "vehicles",
        "user_organizations",
        "invoices",
        "payments",
    }
)
sql_executor = SQLExecutor(session_factory=AsyncSessionLocal)


# -------------------------------------------------
# RESPONDER
# -------------------------------------------------

responder = Responder(llm=llm_client)

# -------------------------------------------------
# ORCHESTRATOR (NEW PIPELINE)
# -------------------------------------------------

orchestrator = Orchestrator(
    chat_history=chat_history,
    context_provider=context_provider,
    planner=planner,
    validator=validator,
    executor=sql_executor,
    responder=responder,
    plan_logger=plan_logger,
)


# -------------------------------------------------
# GATEWAY
# -------------------------------------------------

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