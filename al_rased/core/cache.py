import redis.asyncio as redis
import os
import logging

class CacheManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = None

    async def connect(self):
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        try:
            await self.client.ping()
            logging.info("Connected to Redis.")
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")

    async def close(self):
        if self.client:
            await self.client.close()

    async def set_value(self, key: str, value: str, ex: int = None):
        if self.client:
            try:
                await self.client.set(key, value, ex=ex)
            except Exception as e:
                logging.error(f"Redis set error: {e}")

    async def get_value(self, key: str):
        if self.client:
            try:
                return await self.client.get(key)
            except Exception as e:
                logging.error(f"Redis get error: {e}")
        return None

# Singleton instance
cache = CacheManager()
