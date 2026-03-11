from typing import Any
from conversation.conversation_service import ConversationService
from planning.planner import Planner
from retrieval.data_router import DataRouter

class Orchestrator:
    """
    Coordinates the AI Copilot orchestration pipeline.
    
    Flow:
    1. Save user message via ConversationService
    2. Get recent history/context
    3. Detect intent and build plan via Planner
    4. Retrieve data (structured or vector) via DataRouter
    5. Generate answer via AnswerGenerator (Responder)
    6. Save assistant response via ConversationService
    """
    def __init__(
        self,
        conversation_service: ConversationService,
        planner: Planner,
        data_router: DataRouter,
        responder: Any,  # AnswerGenerator
        context_provider: Any,
        plan_logger: Any,
        failure_logger: Any,
        scope_enforcer: Any,
    ):
        self.conversation_service = conversation_service
        self.planner = planner
        self.data_router = data_router
        self.responder = responder
        self.context_provider = context_provider
        self.plan_logger = plan_logger
        self.failure_logger = failure_logger
        self.scope_enforcer = scope_enforcer

    async def handle(self, message: str, user_id: int, channel: str):
        # 1. save user msg
        await self.conversation_service.save_user_message(
            user_id=user_id,
            text=message,
            channel=channel,
        )

        # 2. get history and context
        history = await self.conversation_service.get_recent_history(
            user_id=user_id,
            channel=channel,
            limit=10,
        )
        
        context = await self.context_provider.get(
            user_id=user_id,
            message=message,
            history=history,
        )

        # 3. plan
        plan = await self.planner.plan(
            message=message,
            history=history,
            context=context,
        )
        plan = self.scope_enforcer.apply(plan, context)
        
        await self.plan_logger.log(
            user_id=user_id,
            channel=channel,
            message=message,
            context=context,
            plan=plan,
        )

        # 4. retrieve data
        data = None
        error = None
        try:
            data = await self.data_router.retrieve(plan)
        except Exception as e:
            print(f"Retrieval error: {e}")
            error = str(e)
            await self.failure_logger.log_failure(
                component="orchestrator_retrieval",
                exception=e,
                meta={
                    "user_id": str(user_id),
                    "plan": plan.__dict__,
                }
            )

        # 5. generate answer
        answer = await self.responder.respond(
            message=message,
            context=context,
            data=data,
            history=history,
            plan=plan,
            error=error,
        )

        # 6. save ai reply
        await self.conversation_service.save_ai_message(
            user_id=user_id,
            text=answer,
            channel=channel,
        )

        return answer