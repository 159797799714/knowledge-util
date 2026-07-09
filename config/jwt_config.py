from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class JWTConfig:
    secret_key: str
    algorithm: str
    expire_minutes: int


jwt_config = JWTConfig(
    secret_key=os.getenv("JWT_SECRET_KEY", ""),
    algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "60")),
)