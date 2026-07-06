import os

from dotenv import load_dotenv

load_dotenv(override=True) #当前项目根目录中的.env优先
load_dotenv() #系统环境变量优先

print(os.getenv("OPENAI_API_KEY"))