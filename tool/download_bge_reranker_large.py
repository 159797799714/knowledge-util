import os
from dotenv import load_dotenv

load_dotenv()

from modelscope.hub.snapshot_download import snapshot_download

cache_dir = os.getenv("MODELSCOPE_CACHE", "./model_cache")
os.makedirs(cache_dir, exist_ok=True)

model_dir = snapshot_download('BAAI/bge-reranker-large', cache_dir=cache_dir)
print(f"模型已下载到：{model_dir}")