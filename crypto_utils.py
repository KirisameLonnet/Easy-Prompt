"""
加密工具模块
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext
import secrets

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CryptoManager:
    """加密管理器"""
    
    def __init__(self, secret_key: str = None):
        """
        初始化加密管理器
        
        Args:
            secret_key: 密钥，如果为None则从环境变量获取或生成
        """
        if secret_key is None:
            secret_key = os.getenv("EASYPROMPT_SECRET_KEY")
            if secret_key is None:
                # 生成新的密钥
                secret_key = Fernet.generate_key().decode()
                print(f"⚠️ 警告: 未设置EASYPROMPT_SECRET_KEY环境变量，使用临时密钥: {secret_key}")
                print("请设置环境变量: export EASYPROMPT_SECRET_KEY='your-secret-key'")
        
        # 验证密钥长度
        if len(secret_key) > 64:
            raise ValueError("密钥长度不能超过64个字符")
        
        self.secret_key = secret_key.encode()
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """获取Fernet加密器"""
        if self._fernet is None:
            # 使用主密钥派生加密密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'easy_prompt_salt',  # 固定盐值，生产环境应该随机生成
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        加密API密钥
        
        Args:
            api_key: 原始API密钥
            
        Returns:
            加密后的API密钥
        """
        if not api_key:
            return ""
        
        fernet = self._get_fernet()
        encrypted_key = fernet.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted_key).decode()
    
    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """
        解密API密钥
        
        Args:
            encrypted_api_key: 加密的API密钥
            
        Returns:
            解密后的API密钥
        """
        if not encrypted_api_key:
            return ""
        
        try:
            fernet = self._get_fernet()
            encrypted_data = base64.urlsafe_b64decode(encrypted_api_key.encode())
            decrypted_key = fernet.decrypt(encrypted_data)
            return decrypted_key.decode()
        except Exception as e:
            print(f"解密API密钥失败: {e}")
            return ""
    
    def hash_password(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 原始密码
            
        Returns:
            哈希后的密码
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 原始密码
            hashed_password: 哈希后的密码
            
        Returns:
            密码是否正确
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        生成安全令牌
        
        Args:
            length: 令牌长度
            
        Returns:
            安全令牌
        """
        return secrets.token_urlsafe(length)

# 全局加密管理器实例
crypto_manager = CryptoManager()

def get_crypto_manager() -> CryptoManager:
    """获取加密管理器实例"""
    return crypto_manager
