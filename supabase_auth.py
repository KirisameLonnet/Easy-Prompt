"""
Supabase认证服务
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from supabase_client import supabase_client
from supabase_models import (
    SupabaseUser, UserProfile, ApiConfigSupabase, 
    LoginRequest, RegisterRequest, AuthResponse,
    PasswordResetRequest, PasswordUpdateRequest
)
from crypto_utils import get_crypto_manager

# JWT配置
SECRET_KEY = os.getenv("EASYPROMPT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 安全方案
security = HTTPBearer()

class SupabaseAuthService:
    """Supabase认证服务"""
    
    def __init__(self):
        if not supabase_client:
            raise ValueError("Supabase配置未初始化，请设置环境变量")
        self.supabase = supabase_client.get_client()
        self.crypto_manager = get_crypto_manager()
    
    async def register(self, register_data: RegisterRequest) -> AuthResponse:
        """用户注册"""
        try:
            # 使用Supabase Auth注册
            auth_response = self.supabase.auth.sign_up({
                "email": register_data.email,
                "password": register_data.password,
                "options": {
                    "data": {
                        "username": register_data.username,
                        "full_name": register_data.full_name
                    }
                }
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="注册失败"
                )
            
            # 创建用户配置文件
            user_profile = UserProfile(
                id=auth_response.user.id,
                user_id=auth_response.user.id,
                username=register_data.username,
                full_name=register_data.full_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 保存到profiles表
            self.supabase.table("profiles").insert(user_profile.dict()).execute()
            
            # 创建SupabaseUser对象
            supabase_user = SupabaseUser(
                id=auth_response.user.id,
                email=auth_response.user.email,
                username=register_data.username,
                full_name=register_data.full_name,
                created_at=datetime.fromisoformat(auth_response.user.created_at.replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(auth_response.user.updated_at.replace('Z', '+00:00')),
                last_sign_in_at=datetime.fromisoformat(auth_response.user.last_sign_in_at.replace('Z', '+00:00')) if auth_response.user.last_sign_in_at else None,
                email_confirmed_at=datetime.fromisoformat(auth_response.user.email_confirmed_at.replace('Z', '+00:00')) if auth_response.user.email_confirmed_at else None,
                phone=auth_response.user.phone,
                role="user",
                status="active"
            )
            
            return AuthResponse(
                user=supabase_user,
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                expires_in=auth_response.session.expires_in,
                token_type="bearer"
            )
            
        except Exception as e:
            print(f"注册错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"注册失败: {str(e)}"
            )
    
    async def login(self, login_data: LoginRequest) -> AuthResponse:
        """用户登录"""
        try:
            # 使用Supabase Auth登录
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="邮箱或密码错误"
                )
            
            # 获取用户配置文件
            profile_response = self.supabase.table("profiles").select("*").eq("user_id", auth_response.user.id).execute()
            
            if not profile_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户配置文件不存在"
                )
            
            profile_data = profile_response.data[0]
            
            # 创建SupabaseUser对象
            supabase_user = SupabaseUser(
                id=auth_response.user.id,
                email=auth_response.user.email,
                username=profile_data.get("username"),
                full_name=profile_data.get("full_name"),
                avatar_url=profile_data.get("avatar_url"),
                created_at=datetime.fromisoformat(auth_response.user.created_at.replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(auth_response.user.updated_at.replace('Z', '+00:00')),
                last_sign_in_at=datetime.fromisoformat(auth_response.user.last_sign_in_at.replace('Z', '+00:00')) if auth_response.user.last_sign_in_at else None,
                email_confirmed_at=datetime.fromisoformat(auth_response.user.email_confirmed_at.replace('Z', '+00:00')) if auth_response.user.email_confirmed_at else None,
                phone=auth_response.user.phone,
                role=profile_data.get("role", "user"),
                status="active"
            )
            
            return AuthResponse(
                user=supabase_user,
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                expires_in=auth_response.session.expires_in,
                token_type="bearer"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"登录错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录失败"
            )
    
    async def logout(self, access_token: str) -> Dict[str, str]:
        """用户登出"""
        try:
            self.supabase.auth.sign_out()
            return {"message": "登出成功"}
        except Exception as e:
            print(f"登出错误: {e}")
            return {"message": "登出成功"}
    
    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """刷新访问令牌"""
        try:
            auth_response = self.supabase.auth.refresh_session(refresh_token)
            
            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌刷新失败"
                )
            
            # 获取用户配置文件
            profile_response = self.supabase.table("profiles").select("*").eq("user_id", auth_response.user.id).execute()
            profile_data = profile_response.data[0] if profile_response.data else {}
            
            supabase_user = SupabaseUser(
                id=auth_response.user.id,
                email=auth_response.user.email,
                username=profile_data.get("username"),
                full_name=profile_data.get("full_name"),
                avatar_url=profile_data.get("avatar_url"),
                created_at=datetime.fromisoformat(auth_response.user.created_at.replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(auth_response.user.updated_at.replace('Z', '+00:00')),
                last_sign_in_at=datetime.fromisoformat(auth_response.user.last_sign_in_at.replace('Z', '+00:00')) if auth_response.user.last_sign_in_at else None,
                email_confirmed_at=datetime.fromisoformat(auth_response.user.email_confirmed_at.replace('Z', '+00:00')) if auth_response.user.email_confirmed_at else None,
                phone=auth_response.user.phone,
                role=profile_data.get("role", "user"),
                status="active"
            )
            
            return AuthResponse(
                user=supabase_user,
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                expires_in=auth_response.session.expires_in,
                token_type="bearer"
            )
            
        except Exception as e:
            print(f"令牌刷新错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌刷新失败"
            )
    
    async def get_current_user(self, access_token: str) -> SupabaseUser:
        """获取当前用户"""
        try:
            # 设置访问令牌
            self.supabase.auth.set_session(access_token, "")
            
            # 获取用户信息
            user_response = self.supabase.auth.get_user()
            
            if not user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的访问令牌"
                )
            
            # 获取用户配置文件
            profile_response = self.supabase.table("profiles").select("*").eq("user_id", user_response.user.id).execute()
            profile_data = profile_response.data[0] if profile_response.data else {}
            
            return SupabaseUser(
                id=user_response.user.id,
                email=user_response.user.email,
                username=profile_data.get("username"),
                full_name=profile_data.get("full_name"),
                avatar_url=profile_data.get("avatar_url"),
                created_at=datetime.fromisoformat(user_response.user.created_at.replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(user_response.user.updated_at.replace('Z', '+00:00')),
                last_sign_in_at=datetime.fromisoformat(user_response.user.last_sign_in_at.replace('Z', '+00:00')) if user_response.user.last_sign_in_at else None,
                email_confirmed_at=datetime.fromisoformat(user_response.user.email_confirmed_at.replace('Z', '+00:00')) if user_response.user.email_confirmed_at else None,
                phone=user_response.user.phone,
                role=profile_data.get("role", "user"),
                status="active"
            )
            
        except Exception as e:
            print(f"获取用户信息错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="获取用户信息失败"
            )
    
    async def reset_password(self, reset_data: PasswordResetRequest) -> Dict[str, str]:
        """重置密码"""
        try:
            self.supabase.auth.reset_password_email(reset_data.email)
            return {"message": "密码重置邮件已发送"}
        except Exception as e:
            print(f"密码重置错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码重置失败"
            )
    
    async def update_password(self, access_token: str, password_data: PasswordUpdateRequest) -> Dict[str, str]:
        """更新密码"""
        try:
            self.supabase.auth.set_session(access_token, "")
            self.supabase.auth.update_user({"password": password_data.new_password})
            return {"message": "密码更新成功"}
        except Exception as e:
            print(f"密码更新错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码更新失败"
            )

# 全局认证服务实例
try:
    auth_service = SupabaseAuthService()
except ValueError as e:
    print(f"⚠️ 警告: Supabase认证服务初始化失败: {e}")
    auth_service = None

# 依赖注入函数
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> SupabaseUser:
    """获取当前用户依赖"""
    return await auth_service.get_current_user(credentials.credentials)
