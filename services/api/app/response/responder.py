class Responder:
    def __init__(self, llm):
        self.llm = llm

    async def respond(self, message, context, data, history):
        prompt = {
            "message": message,
            "context": context,
            "data": data,
            "history": history,
        }

        return await self.llm.generate(prompt)