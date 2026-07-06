from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import time

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:8000"],
    allow_origins=["*"],
    allow_credentials=True,  # ⭐ 允许携带 Cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 模拟数据库 ==========

# 用户数据库
users_db = {
    "user1": {"username": "张三", "password": "123456", "email": "zhangsan@test.com"},
    "user2": {"username": "李四", "password": "654321", "email": "lisi@test.com"},
}

# Session 存储（实际项目中应该用 Redis）
sessions_db = {}


# ========== 数据模型 ==========

class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    username: str
    email: str


# ========== API 接口 ==========

@app.post("/login")
def login(request: LoginRequest, response: Response):
    """
    登录接口：验证用户名密码，创建 Session，设置 Cookie
    """
    # 1. 验证用户名和密码
    user = None
    for user_id, user_info in users_db.items():
        if user_info["username"] == request.username and user_info["password"] == request.password:
            user = user_info
            break

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 2. 创建 Session（生成唯一的 session_id）
    session_id = str(uuid.uuid4())
    sessions_db[session_id] = {
        "user_id": user_id,
        "created_at": time.time(),
        "expires_at": time.time() + 3600  # 1小时后过期
    }

    # 3. ⭐ 设置 Cookie（HttpOnly，更安全）
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=3600,  # 1小时过期
        httponly=True  # ⭐ JavaScript 无法读取（防 XSS 攻击）

    )

    return {
        "code": 0,
        "message": "登录成功",
        "data": {
            "username": user["username"],
            "email": user["email"]
        }
    }


@app.get("/profile")
def get_profile(request: Request):
    """
    获取个人信息：通过 Cookie 中的 session_id 识别用户
    """
    # 1. ⭐ 从 Cookie 中读取 session_id
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="未登录，请先登录")

    # 2. 验证 Session 是否有效
    session = sessions_db.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 无效，请重新登录")

    # 3. 检查是否过期
    if time.time() > session["expires_at"]:
        del sessions_db[session_id]  # 删除过期 Session
        raise HTTPException(status_code=401, detail="Session 已过期，请重新登录")

    # 4. 根据 session_id 找到用户
    user_id = session["user_id"]
    user = users_db.get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 5. 返回用户信息（不返回密码）
    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "username": user["username"],
            "email": user["email"]
        }
    }


@app.post("/logout")
def logout(response: Response):
    """
    退出登录：删除 Cookie 和 Session
    """
    # 删除 Cookie
    response.delete_cookie(key="session_id")

    return {
        "code": 0,
        "message": "已退出登录"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
