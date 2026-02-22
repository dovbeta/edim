class ContextProvider:
    def __init__(self, context_manager):
        self.cm = context_manager

    async def get(self, user_id, message, history):
        return await self.cm.build(user_id, message, history)