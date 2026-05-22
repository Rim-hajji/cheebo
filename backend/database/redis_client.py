"""
Cheebo — Redis client (async + sync)
=====================================
- get_redis()      : client asyncio pour les routes FastAPI / WebSocket
- get_redis_sync() : client synchrone pour les agents LLM (exécutés en thread executor)

Les deux clients sont lazy-init et réutilisés entre les appels.
Si Redis est indisponible, les fonctions lèvent une exception que l'appelant
doit attraper pour basculer sur le comportement in-memory de secours.
"""

import os
import redis as sync_redis
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "agents", ".env"))

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

_async_client: aioredis.Redis | None = None
_sync_client: sync_redis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Retourne le client Redis asyncio (lazy-init, singleton)."""
    global _async_client
    if _async_client is None:
        _async_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _async_client


def get_redis_sync() -> sync_redis.Redis:
    """Retourne le client Redis synchrone (lazy-init, singleton)."""
    global _sync_client
    if _sync_client is None:
        _sync_client = sync_redis.from_url(REDIS_URL, decode_responses=True)
    return _sync_client
