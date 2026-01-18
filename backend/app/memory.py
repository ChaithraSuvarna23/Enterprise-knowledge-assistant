import redis
import json
from typing import List
from fastapi import Query

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

CHAT_TTL_SECONDS = 1800  # 30 minutes
MAX_HISTORY_MESSAGES = 6  # keep last 6 turns only

def get_chat_history(session_id: str, limit: int = MAX_HISTORY_MESSAGES) -> List[dict]:
    key = f"chat:{session_id}"
    messages = redis_client.lrange(key, -limit, -1)
    return [json.loads(m) for m in messages]

def append_message(session_id: str, role: str, content: str):
    key = f"chat:{session_id}"
    redis_client.rpush(
        key,
        json.dumps({"role": role, "content": content})
    )
    redis_client.expire(key, CHAT_TTL_SECONDS)
