import asyncio

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from openai import BaseModel
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

# 3. 定义字典:
# key:会话id session_id
# value:异步队列
task_queues = {}

# 4. 定义异步方法:做包子
async def zuobaozi(session_id: str, query: str):

    # 初始化异步队列
    queue = asyncio.Queue()
    task_queues[session_id] = queue

    # TODO 使用获取到的query去查询大模型，并获取结果
    msg = "大模型的查询结果"

    for i in range(10):

        msg = f"这是会话{session_id}的第{i + 1}个数据，session_id是 {query}"
        # 模拟耗时
        await asyncio.sleep(1)
        # 做一个放一个
        await queue.put(msg)
        print(f"做一个放一个 {session_id}的包子:{i + 1}" )

    # 任务完成(放一个结束标记,表示SSE可以终止了)
    await queue.put(None)


# 定义pydantic数据对象
class QueryRequest(BaseModel):
    query: str
    session_id: str

# 5. 定义submit接口
@app.post("/submit_query")
async def submit_query(req: QueryRequest, background_tasks: BackgroundTasks):

    background_tasks.add_task(zuobaozi, req.session_id, req.query)
    return {"message": f"会话{req.session_id}的包子订单提交成功"}



# 6. 定义SSE接口路由
@app.get("/stream/{session_id}")
async def stream_by_session(session_id: str):
    print(123)
    async def events_generator():
        # 查看当前session_id的异步队列是否存在
        while session_id not in task_queues:
            await asyncio.sleep(0.1)

        # 获取异步队列
        queue = task_queues[session_id]
        # 从异步队列中将包子获取出来
        while True:
            # 取一个
            item = await queue.get()
            # 直到取不出来
            if item is None:
                break

            # 推到前端一个
            # data: 消息\n\n
            yield f"data:{item}\n\n"

    return StreamingResponse(
        events_generator(),
        media_type="text/event-stream"
    )


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8001)