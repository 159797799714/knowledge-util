"""
Redis 工具函数模块

提供 Redis 客户端初始化、用户认证、任务状态管理、SSE 消息队列等功能
所有数据通过 Redis 持久化存储，支持多进程/多实例共享状态
"""
import redis
import json
from typing import Optional, Dict, Any, List

from config.redis_config import redis_config

# Redis 客户端单例实例
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    获取 Redis 客户端实例（单例模式）

    首次调用时创建连接，后续调用复用同一个连接实例
    配置从 config/redis_config.py 读取，支持环境变量覆盖

    Returns:
        redis.Redis: Redis 客户端实例
    """
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
    """
    初始化 Redis 中的用户数据

    在服务启动时调用，将预设用户信息写入 Redis
    用户数据结构: user:{username} (Hash)
        - password: 用户密码（建议生产环境使用加密存储）
        - role: 用户角色（admin/user）
    """
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
    """
    获取用户信息

    Args:
        username: 用户名

    Returns:
        Dict[str, str] or None: 用户信息字典（包含 password, role），用户不存在返回 None
    """
    client = get_redis_client()
    result = client.hgetall(f"user:{username}")
    return result if result else None


def verify_user(username: str, password: str) -> bool:
    """
    验证用户密码

    Args:
        username: 用户名
        password: 待验证的密码

    Returns:
        bool: 验证成功返回 True，失败返回 False
    """
    user_info = get_user_info(username)
    if not user_info:
        return False
    return user_info.get("password") == password


def set_task_status(task_id: str, status: str):
    """
    设置任务状态

    任务状态存储在 Redis Hash: task:{task_id} 的 status 字段中
    支持的状态值: pending / processing / completed / failed

    Args:
        task_id: 任务 ID
        status: 任务状态字符串
    """
    client = get_redis_client()
    client.hset(f"task:{task_id}", "status", status)


def get_task_status(task_id: str) -> str:
    """
    获取任务状态

    Args:
        task_id: 任务 ID

    Returns:
        str: 任务状态字符串，未设置返回空字符串
    """
    client = get_redis_client()
    return client.hget(f"task:{task_id}", "status") or ""


def add_running_task(task_id: str, node_name: str):
    """
    添加正在运行的节点任务

    使用 Redis Set: task:{task_id}:running 存储，自动去重

    Args:
        task_id: 任务 ID
        node_name: 节点名称
    """
    client = get_redis_client()
    client.sadd(f"task:{task_id}:running", node_name)


def remove_running_task(task_id: str, node_name: str):
    """
    移除正在运行的节点任务

    Args:
        task_id: 任务 ID
        node_name: 节点名称
    """
    client = get_redis_client()
    client.srem(f"task:{task_id}:running", node_name)


def get_running_tasks(task_id: str) -> List[str]:
    """
    获取正在运行的节点列表

    Args:
        task_id: 任务 ID

    Returns:
        List[str]: 正在运行的节点名称列表
    """
    client = get_redis_client()
    return list(client.smembers(f"task:{task_id}:running"))


def add_done_task(task_id: str, node_name: str):
    """
    添加已完成的节点任务

    使用 Redis List: task:{task_id}:done 存储，保持完成顺序

    Args:
        task_id: 任务 ID
        node_name: 节点名称
    """
    client = get_redis_client()
    client.rpush(f"task:{task_id}:done", node_name)


def get_done_tasks(task_id: str) -> List[str]:
    """
    获取已完成的节点列表

    Args:
        task_id: 任务 ID

    Returns:
        List[str]: 已完成的节点名称列表（按完成顺序排列）
    """
    client = get_redis_client()
    return client.lrange(f"task:{task_id}:done", 0, -1)


def set_task_result(task_id: str, key: str, value: str):
    """
    设置任务结果字段

    使用 Redis Hash: task:{task_id}:result 存储任意键值对
    常用于存储 answer、error 等结果数据

    Args:
        task_id: 任务 ID
        key: 结果字段名
        value: 结果字段值
    """
    client = get_redis_client()
    client.hset(f"task:{task_id}:result", key, value)


def get_task_result(task_id: str, key: str, default: str = "") -> str:
    """
    获取任务结果字段

    Args:
        task_id: 任务 ID
        key: 结果字段名
        default: 默认值（字段不存在时返回）

    Returns:
        str: 结果字段值，不存在返回默认值
    """
    client = get_redis_client()
    return client.hget(f"task:{task_id}:result", key) or default


def clear_task(task_id: str):
    """
    清理任务所有相关数据

    删除以下 Redis Key:
        - task:{task_id}
        - task:{task_id}:running
        - task:{task_id}:done
        - task:{task_id}:result

    Args:
        task_id: 任务 ID
    """
    client = get_redis_client()
    keys = client.keys(f"task:{task_id}:*")
    if keys:
        client.delete(*keys)
    client.delete(f"task:{task_id}")


def sse_enqueue(session_id: str, event: str, data: Dict[str, Any]):
    """
    将 SSE 消息入队

    使用 Redis List: sse:{session_id} 作为消息队列
    消息格式: JSON {"event": "...", "data": {...}}

    Args:
        session_id: 会话 ID
        event: 事件类型（progress/delta/final/error）
        data: 事件数据
    """
    client = get_redis_client()
    message = json.dumps({"event": event, "data": data})
    client.rpush(f"sse:{session_id}", message)


def sse_dequeue(session_id: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
    """
    从 SSE 队列中取出消息（阻塞方式）

    使用 Redis blpop 实现阻塞读取，避免空轮询
    超时时间内没有消息返回 None

    Args:
        session_id: 会话 ID
        timeout: 阻塞超时时间（秒）

    Returns:
        Dict[str, Any] or None: 消息字典 {"event": "...", "data": {...}}，超时返回 None
    """
    client = get_redis_client()
    result = client.blpop(f"sse:{session_id}", timeout=timeout)
    if result:
        return json.loads(result[1])
    return None


def sse_queue_exists(session_id: str) -> bool:
    """
    检查 SSE 队列是否存在

    Args:
        session_id: 会话 ID

    Returns:
        bool: 队列存在返回 True，否则返回 False
    """
    client = get_redis_client()
    return client.exists(f"sse:{session_id}") > 0


def sse_clear_queue(session_id: str):
    """
    清空 SSE 队列

    Args:
        session_id: 会话 ID
    """
    client = get_redis_client()
    client.delete(f"sse:{session_id}")


def get_session_answer(session_id: str) -> str:
    """
    获取会话的回答结果

    Args:
        session_id: 会话 ID

    Returns:
        str: 回答内容，未设置返回空字符串
    """
    return get_task_result(session_id, "answer", "")


def set_session_answer(session_id: str, answer: str):
    """
    设置会话的回答结果

    Args:
        session_id: 会话 ID
        answer: 回答内容
    """
    set_task_result(session_id, "answer", answer)