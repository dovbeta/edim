from typing import Any
import logging
import time
import uuid

from conversation.conversation_service import ConversationService
from planning.planner import Planner
from planning.scope_enforcer import PolicyError
from retrieval.data_router import DataRouter
from policy.edim_policy import EDIMAccessPolicy
from retrieval.structured_retriever import TooManyStructuredResultsError

logger = logging.getLogger(__name__)

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
        request_id = str(uuid.uuid4())
        t0 = time.perf_counter()

        logger.info(
            "chat.request.start request_id=%s user_id=%s channel=%s message_len=%s",
            request_id,
            user_id,
            channel,
            len(message or ""),
        )
        # 1. save user msg
        try:
            await self.conversation_service.save_user_message(
                user_id=user_id,
                text=message,
                channel=channel,
            )
        except Exception:
            logger.exception("chat.history.save_user_failed request_id=%s", request_id)

        # 2. get history and context
        history = []
        try:
            history = await self.conversation_service.get_recent_history(
                user_id=user_id,
                channel=channel,
                limit=10,
            )
        except Exception:
            logger.exception("chat.history.load_failed request_id=%s", request_id)

        context = {}
        try:
            context = await self.context_provider.get(
                user_id=user_id,
                message=message,
                history=history,
            )
        except Exception:
            logger.exception("chat.context.build_failed request_id=%s", request_id)
            context = {}

        context["request_id"] = request_id
        context["role"] = EDIMAccessPolicy.resolve_role(context)

        scope = (context or {}).get("scope", {}) or {}
        logger.info(
            "chat.context.ready request_id=%s role=%s building_ids=%s org_ids=%s",
            request_id,
            context.get("role"),
            len(scope.get("building_ids") or []),
            len(scope.get("organization_ids") or []),
        )

        # 3. plan
        error = None
        try:
            tp = time.perf_counter()
            plan = await self.planner.plan(
                message=message,
                history=history,
                context=context,
            )
            plan = self.scope_enforcer.apply(plan, context)
            logger.info(
                "chat.plan.ready request_id=%s intent=%s sources=%s needs_more_info=%s has_sql=%s plan_ms=%s",
                request_id,
                getattr(plan, "intent", None),
                getattr(plan, "sources", None),
                getattr(plan, "needs_more_info", None),
                bool(getattr(plan, "structured_query", None)),
                int((time.perf_counter() - tp) * 1000),
            )
            if getattr(plan, "structured_query", None):
                sql_preview = " ".join(plan.structured_query.split())
                if len(sql_preview) > 600:
                    sql_preview = sql_preview[:600] + "…"
                logger.info(
                    "chat.plan.sql request_id=%s sql=%s params_keys=%s",
                    request_id,
                    sql_preview,
                    sorted((plan.structured_params or {}).keys()),
                )
        except PolicyError as e:
            # controlled policy/tenant violation – no data retrieval, just explanation
            plan = None
            error = str(e)
            logger.warning("chat.plan.policy_block request_id=%s error=%s", request_id, error)
            await self.failure_logger.log_failure(
                component="orchestrator_policy",
                exception=e,
                meta={
                    "user_id": str(user_id),
                    "channel": channel,
                }
            )
        except Exception as e:
            plan = None
            error = str(e)
            logger.exception("chat.plan.failed request_id=%s error=%s", request_id, error)
            if self.failure_logger:
                await self.failure_logger.log_failure(
                    component="orchestrator_plan",
                    exception=e,
                    meta={"user_id": str(user_id), "channel": channel},
                )
        else:
            await self.plan_logger.log(
                user_id=user_id,
                channel=channel,
                message=message,
                context=context,
                plan=plan,
            )

        # 4. retrieve data
        data = None
        if error is None and plan is not None:
            try:
                tr = time.perf_counter()
                data = await self.data_router.retrieve(plan, context=context)
                logger.info(
                    "chat.retrieve.ok request_id=%s retrieve_ms=%s",
                    request_id,
                    int((time.perf_counter() - tr) * 1000),
                )
            except TooManyStructuredResultsError as e:
                data = None
                error = (
                    "Знайдено забагато записів. "
                    "Будь ласка, уточніть запит (будинок/підʼїзд/квартира/ПІБ/номер авто), "
                    "щоб отримати коротку відповідь."
                )
                logger.warning("chat.retrieve.too_many_results request_id=%s error=%s", request_id, str(e))
            except Exception as e:
                error = str(e)
                logger.exception("chat.retrieve.failed request_id=%s error=%s", request_id, error)
                await self.failure_logger.log_failure(
                    component="orchestrator_retrieval",
                    exception=e,
                    meta={
                        "user_id": str(user_id),
                        "plan": getattr(plan, "__dict__", None),
                    }
                )

        # 5. generate answer
        ta = time.perf_counter()
        answer = await self.responder.respond(
            message=message,
            context=context,
            data=data,
            history=history,
            plan=plan,
            error=error,
        )
        logger.info(
            "chat.answer.ready request_id=%s answer_len=%s answer_ms=%s error=%s total_ms=%s",
            request_id,
            len(answer or ""),
            int((time.perf_counter() - ta) * 1000),
            bool(error),
            int((time.perf_counter() - t0) * 1000),
        )

        # 6. save ai reply with metadata
        found_info = False
        if error is None:
            if isinstance(data, list):
                found_info = len(data) > 0
            elif isinstance(data, dict):
                # any non-empty structured/vector result
                found_info = bool(data)

        intent = getattr(plan, "intent", None) if plan else None
        # Heuristic: intents, що стосуються ЖКГ / будинку
        housing_intents = {
            "resident_address",
            "resident_debt",
            "contacts",
            "vehicles",
            "units",
            "organizations",
            "buildings",
            "roles",
            "services",
            "announcements",
            "rules",
            "faq",
        }
        is_housing_utility = intent in housing_intents

        meta = {
            "request_id": request_id,
            "found_info": found_info,
            "is_housing_utility": is_housing_utility,
        }

        try:
            await self.conversation_service.save_ai_message(
                user_id=user_id,
                text=answer,
                channel=channel,
                intent=intent,
                meta=meta,
            )
        except Exception:
            logger.exception("chat.history.save_ai_failed request_id=%s", request_id)

        return answer