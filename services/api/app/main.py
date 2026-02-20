from fastapi import FastAPI
from db.session import AsyncSessionLocal
from gateway.chat_gateway import ChatGateway
from orchestrator import Orchestrator
from core.chat_request import ChatRequest
from core.contact_request import ContactRequest

app = FastAPI(title="E-Dim Copilot API")

# -------------------------------------------------
# DEPENDENCIES
# -------------------------------------------------

def get_session_factory():
    return AsyncSessionLocal


orchestrator = Orchestrator()
gateway = ChatGateway(
    session_factory=get_session_factory(),
    orchestrator=orchestrator,
)
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