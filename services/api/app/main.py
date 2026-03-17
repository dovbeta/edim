from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from db.session import AsyncSessionLocal

# context
from context.context_manager import ContextManager
from context.context_provider import ContextProvider

# conversation
from conversation.conversation_service import ConversationService

# chat history repository (still needed)
from chat_history.repository import ChatHistoryRepository

# failure logger
from failure_logger.repository import FailureLoggerRepository
from failure_logger.service import FailureLoggerService

# llm
from llm.gemini import GeminiClient
from llm.openai_embed import OpenAIEmbeddingClient
from planning.scope_enforcer import ScopeEnforcer
from policy.prompt_builder import EDIMPromptBuilder
from planning.plan_logger import PlanLogger

# planning
from planning.planner import Planner, DATA_CATALOG

# retrieval
from retrieval.data_router import DataRouter
from retrieval.structured_retriever import StructuredRetriever
from retrieval.vector_retriever import VectorRetriever
from execution.sql_validator import SQLValidator
from execution.sql_executor import SQLExecutor
from planning.prompts import PlannerPromptBuilder
from planning.sql_schema import SQL_SCHEMA

# response
from response.responder import Responder

# orchestrator + gateway
from orchestrator.orchestrator import Orchestrator
from gateway.chat_gateway import ChatGateway
from gateway.identity_service import IdentityService

from core.settings import settings

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

mongo_client = AsyncIOMotorClient(settings.mongo_url)
mongo_db = mongo_client[settings.mongo_db]
mongo_messages = mongo_db["messages"]
mongo_knowledge = mongo_db["knowledge"]

# -------------------------------------------------
# CONVERSATION SERVICE
# -------------------------------------------------

chat_history_repo = ChatHistoryRepository(mongo_messages)
conversation_service = ConversationService(chat_history_repo)

# -------------------------------------------------
# MONGO FAILURE LOGS
# -------------------------------------------------

mongo_failures = mongo_db["failures"]
failure_logger_repo = FailureLoggerRepository(mongo_failures)
failure_logger = FailureLoggerService(failure_logger_repo)


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

planner_prompt_builder = PlannerPromptBuilder(schema=SQL_SCHEMA, data_catalog=DATA_CATALOG)

planner = Planner(
    llm=llm_client,
    prompt_builder=planner_prompt_builder,
)
scope_enforcer = ScopeEnforcer()
planner_logs = mongo_db["planner_logs"]
plan_logger = PlanLogger(planner_logs)


# -------------------------------------------------
# RETRIEVAL (STRUCTURED + VECTOR)
# -------------------------------------------------

validator = SQLValidator(
    allowed_tables={
        "users",
        "units",
        "units_extended",
        "buildings",
        "organizations",
        "vehicles",
        "user_organizations",
        "user_units",
        "invoices",
        "payments",
        "unit_residents",
    }
)
sql_executor = SQLExecutor(session_factory=AsyncSessionLocal)

structured_retriever = StructuredRetriever(executor=sql_executor, validator=validator)

embedding_client = OpenAIEmbeddingClient()
vector_retriever = VectorRetriever(
    collection=mongo_knowledge,
    embedding_client=embedding_client
)
data_router = DataRouter(structured_retriever=structured_retriever, vector_retriever=vector_retriever)


# -------------------------------------------------
# RESPONDER
# -------------------------------------------------

responder = Responder(llm=llm_client)

# -------------------------------------------------
# ORCHESTRATOR (NEW PIPELINE)
# -------------------------------------------------

orchestrator = Orchestrator(
    conversation_service=conversation_service,
    planner=planner,
    data_router=data_router,
    responder=responder,
    context_provider=context_provider,
    plan_logger=plan_logger,
    failure_logger=failure_logger,
    scope_enforcer=scope_enforcer,
)


# -------------------------------------------------
# GATEWAY
# -------------------------------------------------

identity_service = IdentityService()

gateway = ChatGateway(
    session_factory=get_session_factory(),
    orchestrator=orchestrator,
    failure_logger=failure_logger,
    identity_service=identity_service,
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