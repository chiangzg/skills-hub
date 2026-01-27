"""
安全模块：密码加密、敏感数据加密
"""
from cryptography.fernet import Fernet
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()


class PasswordManager:
    """密码加密管理"""

    def __init__(self):
        # 使用 argon2 替代 bcrypt，避免 72 字节限制
        self.context = CryptContext(
            schemes=["argon2"],
            deprecated="auto"
        )

    def hash_password(self, password: str) -> str:
        """生成密码哈希"""
        return self.context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.context.verify(plain_password, hashed_password)


class Encryption:
    """敏感数据加密（如 GitLab Token）"""

    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            # 如果没有配置密钥，生成一个新的
            key = Fernet.generate_key()
            print(f"Generated new encryption key: {key.decode()}")
            print("Please add this to your .env file: ENCRYPTION_KEY=" + key.decode())
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """加密数据"""
        if not data:
            return ""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """解密数据"""
        if not encrypted:
            return ""
        return self.cipher.decrypt(encrypted.encode()).decode()


# 全局实例
password_manager = PasswordManager()
encryption = Encryption()


def generate_encryption_key() -> str:
    """生成新的加密密钥"""
    return Fernet.generate_key().decode()
