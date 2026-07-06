import asyncio

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

# 1. 创建应用
app = FastAPI()

# 2. 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的源
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],  # 允许的请求头
)

# 4. 定义SSE接口路由
@app.get("/stream/{session_id}")
async def stream_by_session(session_id: str):

    # 3. 定义生成器函数
    async def events_generator():
        for i in range(5):
            # SSE事件推流的固定格式 data: 内容\n\n
            yield f"data: 这是会话{session_id}的第{i + 1}条消息\n\n"
            await asyncio.sleep(1)
        yield "data: [END]\n\n"

    async def error_events_generator():
        yield f"data: {session_id}是无效会话\n\n"
        yield "data: [END]\n\n"

    if session_id == "100":
        return StreamingResponse(
            events_generator(),
            media_type="text/event-stream"
        )
    else:
        return StreamingResponse(
            error_events_generator(),
            media_type="text/event-stream"
        )


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8001)