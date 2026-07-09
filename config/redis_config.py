from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str
    decode_responses: bool = True


redis_config = RedisConfig(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    password=os.getenv("REDIS_PASSWORD", ""),
    decode_responses=True,
)