"""
用户数据库管理模块
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import uuid

from auth_models import User, UserCreate, UserUpdate, UserResponse, EncryptedApiConfig
from crypto_utils import get_crypto_manager

class UserDatabase:
    """用户数据库管理器"""
    
    def __init__(self, db_dir: str = "./user_data"):
        """
        初始化用户数据库
        
        Args:
            db_dir: 数据库目录
        """
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(exist_ok=True)
        
        # 用户数据文件
        self.users_file = self.db_dir / "users.json"
        self.api_configs_file = self.db_dir / "api_configs.json"
        
        # 内存缓存
        self._users_cache: Dict[str, User] = {}
        self._api_configs_cache: Dict[str, EncryptedApiConfig] = {}
        
        # 加载数据
        self._load_data()
    
    def _load_data(self):
        """加载数据到内存"""
        # 加载用户数据
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    for user_data in users_data:
                        user = User(**user_data)
                        self._users_cache[user.id] = user
            except Exception as e:
                print(f"加载用户数据失败: {e}")
        
        # 加载API配置数据
        if self.api_configs_file.exists():
            try:
                with open(self.api_configs_file, 'r', encoding='utf-8') as f:
                    configs_data = json.load(f)
                    for config_data in configs_data:
                        config = EncryptedApiConfig(**config_data)
                        self._api_configs_cache[config.id] = config
            except Exception as e:
                print(f"加载API配置数据失败: {e}")
    
    def _save_users(self):
        """保存用户数据到文件"""
        try:
            users_data = [user.dict() for user in self._users_cache.values()]
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存用户数据失败: {e}")
    
    def _save_api_configs(self):
        """保存API配置数据到文件"""
        try:
            configs_data = [config.dict() for config in self._api_configs_cache.values()]
            with open(self.api_configs_file, 'w', encoding='utf-8') as f:
                json.dump(configs_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存API配置数据失败: {e}")
    
    # 用户管理方法
    def create_user(self, user_create: UserCreate) -> User:
        """
        创建用户
        
        Args:
            user_create: 用户创建数据
            
        Returns:
            创建的用户
        """
        # 检查用户名是否已存在
        if self.get_user_by_username(user_create.username):
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        if self.get_user_by_email(user_create.email):
            raise ValueError("邮箱已存在")
        
        # 创建用户
        crypto_manager = get_crypto_manager()
        user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=crypto_manager.hash_password(user_create.password)
        )
        
        self._users_cache[user.id] = user
        self._save_users()
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self._users_cache.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        for user in self._users_cache.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        for user in self._users_cache.values():
            if user.email == email:
                return user
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户身份
        
        Args:
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            验证成功返回用户，失败返回None
        """
        # 尝试通过用户名查找
        user = self.get_user_by_username(username)
        
        # 如果用户名没找到，尝试通过邮箱查找
        if not user:
            user = self.get_user_by_email(username)
        
        if not user:
            return None
        
        # 验证密码
        crypto_manager = get_crypto_manager()
        if not crypto_manager.verify_password(password, user.hashed_password):
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        user.updated_at = datetime.now()
        self._save_users()
        
        return user
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            user_update: 更新数据
            
        Returns:
            更新后的用户
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # 检查用户名冲突
        if user_update.username and user_update.username != user.username:
            if self.get_user_by_username(user_update.username):
                raise ValueError("用户名已存在")
        
        # 检查邮箱冲突
        if user_update.email and user_update.email != user.email:
            if self.get_user_by_email(user_update.email):
                raise ValueError("邮箱已存在")
        
        # 更新字段
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now()
        self._save_users()
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        if user_id not in self._users_cache:
            return False
        
        # 删除用户
        del self._users_cache[user_id]
        
        # 删除用户的API配置
        self.delete_user_api_configs(user_id)
        
        self._save_users()
        return True
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """
        列出用户
        
        Args:
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            用户列表
        """
        users = list(self._users_cache.values())[skip:skip + limit]
        return [UserResponse(**user.dict()) for user in users]
    
    # API配置管理方法
    def save_api_config(self, user_id: str, api_config: Dict[str, Any]) -> EncryptedApiConfig:
        """
        保存用户的API配置
        
        Args:
            user_id: 用户ID
            api_config: API配置
            
        Returns:
            加密的API配置
        """
        crypto_manager = get_crypto_manager()
        
        # 加密API密钥
        encrypted_api_key = crypto_manager.encrypt_api_key(api_config.get("api_key", ""))
        
        # 创建加密配置
        encrypted_config = EncryptedApiConfig(
            user_id=user_id,
            api_type=api_config.get("api_type", "openai"),
            encrypted_api_key=encrypted_api_key,
            base_url=api_config.get("base_url", ""),
            model=api_config.get("model", ""),
            evaluator_model=api_config.get("evaluator_model"),
            temperature=api_config.get("temperature", 0.7),
            max_tokens=api_config.get("max_tokens", 4000),
            nsfw_mode=api_config.get("nsfw_mode", False)
        )
        
        self._api_configs_cache[encrypted_config.id] = encrypted_config
        self._save_api_configs()
        
        return encrypted_config
    
    def get_user_api_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户的API配置（解密后）
        
        Args:
            user_id: 用户ID
            
        Returns:
            解密后的API配置
        """
        # 查找用户的API配置
        for config in self._api_configs_cache.values():
            if config.user_id == user_id:
                crypto_manager = get_crypto_manager()
                
                # 解密API密钥
                decrypted_api_key = crypto_manager.decrypt_api_key(config.encrypted_api_key)
                
                return {
                    "api_type": config.api_type,
                    "api_key": decrypted_api_key,
                    "base_url": config.base_url,
                    "model": config.model,
                    "evaluator_model": config.evaluator_model,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "nsfw_mode": config.nsfw_mode
                }
        
        return None
    
    def update_user_api_config(self, user_id: str, api_config: Dict[str, Any]) -> Optional[EncryptedApiConfig]:
        """
        更新用户的API配置
        
        Args:
            user_id: 用户ID
            api_config: 新的API配置
            
        Returns:
            更新后的加密配置
        """
        # 删除旧配置
        self.delete_user_api_configs(user_id)
        
        # 保存新配置
        return self.save_api_config(user_id, api_config)
    
    def delete_user_api_configs(self, user_id: str) -> bool:
        """
        删除用户的所有API配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        configs_to_delete = [
            config_id for config_id, config in self._api_configs_cache.items()
            if config.user_id == user_id
        ]
        
        for config_id in configs_to_delete:
            del self._api_configs_cache[config_id]
        
        if configs_to_delete:
            self._save_api_configs()
            return True
        
        return False

# 全局数据库实例
user_db = UserDatabase()

def get_user_database() -> UserDatabase:
    """获取用户数据库实例"""
    return user_db
