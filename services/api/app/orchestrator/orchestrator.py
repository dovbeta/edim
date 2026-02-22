class Orchestrator:
    def __init__(
        self,
        chat_history,
        context_provider,
        planner,
        validator,
        executor,
        responder,
        plan_logger,
    ):
        self.chat_history = chat_history
        self.context_provider = context_provider
        self.planner = planner
        self.validator = validator
        self.executor = executor
        self.responder = responder
        self.plan_logger = plan_logger

    async def handle(self, message: str, user_id: int, channel: str):

        # 1 save user msg
        await self.chat_history.save_user_message(
            user_id=user_id,
            channel=channel,
            text=message,
        )

        # 2 history
        history = await self.chat_history.get_context_messages(
            user_id=user_id,
            channel=channel,
            limit=8,
            minutes=60,
        )

        # 3 domain context
        context = await self.context_provider.get(
            user_id=user_id,
            message=message,
            history=history,
        )

        # 4 plan
        plan = await self.planner.plan(
            message=message,
            context=context,
            history=history,
        )
        await self.plan_logger.log(
            user_id=user_id,
            channel=channel,
            message=message,
            context=context,
            plan=plan,
        )
        print(plan)

        data = None

        # 5 sql path
        if plan.needs_sql and plan.sql:
            self.validator.validate(plan.sql)

            data = await self.executor.run(
                plan.sql,
                plan.params,
            )

        # 6 respond
        answer = await self.responder.respond(
            message=message,
            context=context,
            data=data,
            history=history,
        )

        # 7 save assistant
        await self.chat_history.save_assistant_message(
            user_id=user_id,
            channel=channel,
            text=answer,
        )

        return answer