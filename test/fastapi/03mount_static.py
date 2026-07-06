import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

# 1. 组装静态资源所在的路径
app = FastAPI()
path = Path(__file__)
static_dir = path.parent / "static"

# 2. 将静态资源路径挂载到自定义路由中
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)