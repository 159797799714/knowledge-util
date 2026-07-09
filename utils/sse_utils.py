import json
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import Request

from .redis_utils import sse_enqueue, sse_dequeue, sse_queue_exists, sse_clear_queue


class SSEEvent:
    READY = "ready"
    PROGRESS = "progress"
    DELTA = "delta"
    FINAL = "final"
    ERROR = "error"
    CLOSE = "__close__"


def get_sse_queue(session_id: str) -> bool:
    return sse_queue_exists(session_id)


def create_sse_queue(session_id: str):
    pass


def remove_sse_queue(session_id: str):
    sse_clear_queue(session_id)


def _sse_pack(event: str, data: Dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def push_to_session(session_id: str, event: str, data: Dict[str, Any]):
    sse_enqueue(session_id, event, data)


async def sse_generator(session_id: str, request: Request) -> AsyncGenerator[str, None]:
    if not sse_queue_exists(session_id):
        return

    loop = asyncio.get_running_loop()
    try:
        yield _sse_pack("ready", {})

        while True:
            if await request.is_disconnected():
                break

            try:
                msg = await loop.run_in_executor(None, sse_dequeue, session_id, 1.0)
            except Exception:
                continue

            if msg is None:
                continue

            event = msg.get("event")
            data = msg.get("data")

            if event == "__close__":
                break

            yield _sse_pack(event, data)
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        return
    finally:
        remove_sse_queue(session_id)