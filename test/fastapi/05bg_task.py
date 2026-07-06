import asyncio
import time

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from starlette.middleware.cors import CORSMiddleware

# 1. 创建主程序
app = FastAPI()

# 2. 设置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# 3. 定义一个耗时的异步任务
async def send_email(email: str, message: str):
    while True:
        print(f"异步任务正在发送邮件...目标{email}; 内容:{message} {time.asctime()}")
        await asyncio.sleep(1)


# 4. 定义一个接口，接收邮箱，并将邮箱地址和发送的内容添加到后台任务队列
@app.post("/send-task/{email}")
async def send_task(email: str, background_tasks: BackgroundTasks):

    print(f"开始处理异步任务...目标{email} {time.asctime()}")

    # 1. 添加后台任务到任务队列
    background_tasks.add_task(send_email, email, "hello")

    print(f"异步任务已添加到队列...目标{email} {time.asctime()}")

    return {"message": "异步任务任务已启动"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)