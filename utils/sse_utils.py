import json
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import Request

from .redis_utils import sse_enqueue, sse_dequeue, sse_queue_exists, sse_clear_queue


class SSEEvent:
    READY = "ready"         # 连接建立
    PROGRESS = "progress"   # 任务节点进度
    DELTA = "delta"         # LLM 流式输出增量
    FINAL = "final"         # 最终完整答案
    ERROR = "error"         # 错误信息
    CLOSE = "__close__"     # 关闭连接信号


# Redis持久化 SSE 会话队列存储
# Key: session_id, Value: Redis List

def get_sse_queue(session_id: str) -> bool:
    """获取指定 session 的队列是否存在"""
    return sse_queue_exists(session_id)


def create_sse_queue(session_id: str):
    """创建并注册一个新的 SSE 队列（Redis方式不需要显式创建）"""
    pass


def remove_sse_queue(session_id: str):
    """移除指定 session 的队列"""
    sse_clear_queue(session_id)


def _sse_pack(event: str, data: Dict[str, Any]) -> str:
    """打包 SSE 消息格式"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def push_to_session(session_id: str, event: str, data: Dict[str, Any]):
    """
    通过 session_id 推送事件
    """
    sse_enqueue(session_id, event, data)


async def sse_generator(session_id: str, request: Request) -> AsyncGenerator[str, None]:
    """
    SSE 生成器，用于 FastAPI 的 StreamingResponse
    """
    if not sse_queue_exists(session_id):
        # 如果没有对应的队列，直接结束
        return

    loop = asyncio.get_running_loop()
    try:
        # 发送连接建立信号
        yield _sse_pack("ready", {})

        while True:
            # 若客户端断开，尽快退出
            if await request.is_disconnected():
                break

            try:
                # 使用 run_in_executor 避免阻塞 async 事件循环
                msg = await loop.run_in_executor(None, sse_dequeue, session_id, 1.0)
            except Exception:
                continue

            if msg is None:
                continue

            event = msg.get("event")
            data = msg.get("data")

            # 特殊关闭事件
            if event == "__close__":
                break

            yield _sse_pack(event, data)
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        # 生成器被取消/对端断开：静默退出
        return
    finally:
        # 清理资源
        remove_sse_queue(session_id)