import os
import redis
from pymongo import MongoClient
import psycopg2


class ContextManager:
    def __init__(self):
        self.pg = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )

        self.mongo = MongoClient(os.getenv("MONGO_URL"))
        self.redis = redis.Redis(host=os.getenv("REDIS_HOST"), port=6379)

    async def get_context(self, message: str):
        return {"user": "demo", "message": message}