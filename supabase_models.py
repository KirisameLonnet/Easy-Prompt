"""
Supabase用户相关模型
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class SupabaseUser(BaseModel):
    """Supabase用户模型"""
    id: str
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_sign_in_at: Optional[datetime] = None
    email_confirmed_at: Optional[datetime] = None
    phone: Optional[str] = None
    role: str = "user"
    status: str = "active"

class UserProfile(BaseModel):
    """用户配置文件"""
    id: str
    user_id: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferences: dict = {}
    created_at: datetime
    updated_at: datetime

class ApiConfigSupabase(BaseModel):
    """Supabase中的API配置模型"""
    id: str
    user_id: str
    api_type: str
    encrypted_api_key: str
    base_url: str
    model: str
    evaluator_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    nsfw_mode: bool = False
    created_at: datetime
    updated_at: datetime

class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr
    password: str
    username: str
    full_name: Optional[str] = None

class AuthResponse(BaseModel):
    """认证响应"""
    user: SupabaseUser
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"

class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: EmailStr

class PasswordUpdateRequest(BaseModel):
    """密码更新请求"""
    password: str
    new_password: str
