class Orchestrator:
    def __init__(self, llm, context_manager, chat_history):
        self.llm = llm
        self.context_manager = context_manager
        self.chat_history = chat_history

    async def handle(self, message: str, user_id: int, channel: str):

        # 1️⃣ save user message
        await self.chat_history.save_user_message(
            user_id=user_id,
            channel=channel,
            text=message,
        )

        # 2️⃣ get recent history
        history = await self.chat_history.get_context_messages(
            user_id=user_id,
            channel=channel,
            limit=8,
            minutes=60,
        )

        # 3️⃣ build domain context
        context = await self.context_manager.build(
            user_id=user_id,
            message=message,
            chat_history=history,
        )

        # 4️⃣ call LLM
        answer = await self.llm.generate(
            message=message,
            context=context,
            history=history,
        )

        # 5️⃣ save assistant message
        await self.chat_history.save_assistant_message(
            user_id=user_id,
            channel=channel,
            text=answer,
        )

        return answer