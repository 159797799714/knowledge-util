import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# 1. 创建主程序
app = FastAPI()


# 2. 设置跨域响应头
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000"
    ],#允许所有前端服务器获取我的响应
    allow_credentials=True, #允许前端携带cookie到后端
    allow_methods=["*"], #允许所有方法 GET\POST\PUT\DELETE
    allow_headers=["*"] #允许所有请求头
)

@app.get("/api/data")
async def get_data():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)