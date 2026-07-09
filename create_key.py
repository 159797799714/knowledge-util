
# Python 生成随机密钥  用于JWT认证
import secrets
print(secrets.token_hex(32))  # 生成64位十六进制随机字符串