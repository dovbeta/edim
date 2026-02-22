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
            "needs_sql": plan.needs_sql,
            "sql": plan.sql,
            "params": plan.params,
            "buildings": list(set(buildings)),
            "created_at": datetime.utcnow(),
        }

        await self.collection.insert_one(doc)