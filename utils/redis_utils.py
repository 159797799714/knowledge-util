import redis
import json
from typing import Optional, Dict, Any, List

from config.redis_config import redis_config

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            password=redis_config.password,
            decode_responses=redis_config.decode_responses,
            socket_timeout=10,
            socket_connect_timeout=10,
        )
    return _redis_client


def init_redis_users():
    client = get_redis_client()
    users = {
        "admin": {
            "password": "admin123",
            "role": "admin"
        },
        "user": {
            "password": "user123",
            "role": "user"
        }
    }
    for username, info in users.items():
        client.hset(f"user:{username}", mapping=info)


def get_user_info(username: str) -> Optional[Dict[str, str]]:
    client = get_redis_client()
    result = client.hgetall(f"user:{username}")
    return result if result else None


def verify_user(username: str, password: str) -> bool:
    user_info = get_user_info(username)
    if not user_info:
        return False
    return user_info.get("password") == password


def set_task_status(task_id: str, status: str):
    client = get_redis_client()
    client.hset(f"task:{task_id}", "status", status)


def get_task_status(task_id: str) -> str:
    client = get_redis_client()
    return client.hget(f"task:{task_id}", "status") or ""


def add_running_task(task_id: str, node_name: str):
    client = get_redis_client()
    client.sadd(f"task:{task_id}:running", node_name)


def remove_running_task(task_id: str, node_name: str):
    client = get_redis_client()
    client.srem(f"task:{task_id}:running", node_name)


def get_running_tasks(task_id: str) -> List[str]:
    client = get_redis_client()
    return list(client.smembers(f"task:{task_id}:running"))


def add_done_task(task_id: str, node_name: str):
    client = get_redis_client()
    client.rpush(f"task:{task_id}:done", node_name)


def get_done_tasks(task_id: str) -> List[str]:
    client = get_redis_client()
    return client.lrange(f"task:{task_id}:done", 0, -1)


def set_task_result(task_id: str, key: str, value: str):
    client = get_redis_client()
    client.hset(f"task:{task_id}:result", key, value)


def get_task_result(task_id: str, key: str, default: str = "") -> str:
    client = get_redis_client()
    return client.hget(f"task:{task_id}:result", key) or default


def clear_task(task_id: str):
    client = get_redis_client()
    keys = client.keys(f"task:{task_id}:*")
    if keys:
        client.delete(*keys)
    client.delete(f"task:{task_id}")


def sse_enqueue(session_id: str, event: str, data: Dict[str, Any]):
    client = get_redis_client()
    message = json.dumps({"event": event, "data": data})
    client.rpush(f"sse:{session_id}", message)


def sse_dequeue(session_id: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
    client = get_redis_client()
    result = client.blpop(f"sse:{session_id}", timeout=timeout)
    if result:
        return json.loads(result[1])
    return None


def sse_queue_exists(session_id: str) -> bool:
    client = get_redis_client()
    return client.exists(f"sse:{session_id}") > 0


def sse_clear_queue(session_id: str):
    client = get_redis_client()
    client.delete(f"sse:{session_id}")


def get_session_answer(session_id: str) -> str:
    return get_task_result(session_id, "answer", "")


def set_session_answer(session_id: str, answer: str):
    set_task_result(session_id, "answer", answer)