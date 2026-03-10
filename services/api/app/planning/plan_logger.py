from datetime import datetime


class PlanLogger:
    def __init__(self, collection):
        self.collection = collection

    async def log(self, user_id, channel, message, context, plan):

        buildings = []
        for p in context.get("properties", []):
            b = p.get("building", {}).get("id")
            if b:
                buildings.append(b)

        doc = {
            "user_id": str(user_id),
            "channel": channel,
            "message": message,

            "intent": plan.intent,
            "sources": plan.sources,

            "structured_query": plan.structured_query,
            "params": plan.structured_params,

            "needs_more_info": plan.needs_more_info,

            "buildings": list(set(buildings)),

            "created_at": datetime.utcnow(),
        }

        await self.collection.insert_one(doc)