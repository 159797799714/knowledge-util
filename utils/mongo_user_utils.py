import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


class UserMongoTool:
    def __init__(self):
        try:
            self.mongo_url = os.getenv("MONGO_URL")
            self.db_name = os.getenv("MONGO_DB_NAME")
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]
            self.users = self.db["users"]
            self.users.create_index("username", unique=True)
            logging.info(f"Successfully connected to MongoDB users collection: {self.db_name}")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise


_user_mongo_tool = UserMongoTool()


def get_user_mongo_tool() -> UserMongoTool:
    global _user_mongo_tool
    if _user_mongo_tool is None:
        _user_mongo_tool = UserMongoTool()
    return _user_mongo_tool


class RegisterResult:
    SUCCESS = "success"
    USER_EXISTS = "user_exists"
    ERROR = "error"


def register_user(username: str, password: str, role: str = "user") -> str:
    mongo_tool = get_user_mongo_tool()
    try:
        existing_user = mongo_tool.users.find_one({"username": username})
        if existing_user:
            logging.info(f"User registration failed: {username} already exists")
            return RegisterResult.USER_EXISTS

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user_data = {
            "username": username,
            "password": hashed_password,
            "role": role,
            "created_at": datetime.now().timestamp(),
            "updated_at": datetime.now().timestamp()
        }
        mongo_tool.users.insert_one(user_data)
        logging.info(f"User registered successfully: {username}")
        return RegisterResult.SUCCESS
    except Exception as e:
        logging.error(f"Error registering user {username}: {e}")
        return RegisterResult.ERROR


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    mongo_tool = get_user_mongo_tool()
    try:
        return mongo_tool.users.find_one({"username": username})
    except Exception as e:
        logging.error(f"Error getting user {username}: {e}")
        return None


def verify_password(username: str, password: str) -> bool:
    user = get_user_by_username(username)
    if not user:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), user["password"])
    except Exception as e:
        logging.error(f"Error verifying password for user {username}: {e}")
        return False


def init_default_users():
    """
    初始化默认用户
    服务启动时调用，确保默认用户存在
    已添加异常处理，避免重复启动时报错
    """
    default_users = [
        {"username": "admin", "password": "admin123", "role": "admin"},
        {"username": "user", "password": "user123", "role": "user"}
    ]
    for user in default_users:
        try:
            result = register_user(user["username"], user["password"], user["role"])
            if result == RegisterResult.SUCCESS:
                logging.info(f"Default user created: {user['username']}")
            elif result == RegisterResult.USER_EXISTS:
                logging.info(f"Default user already exists: {user['username']}")
            elif result == RegisterResult.ERROR:
                logging.warning(f"Failed to create default user: {user['username']}")
        except Exception as e:
            # 捕获可能的数据库异常（如唯一索引冲突等）
            logging.warning(f"Error initializing default user {user['username']}: {e}. This is expected if user already exists.")