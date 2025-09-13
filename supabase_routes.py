"""
Supabase认证API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase_auth import auth_service, get_current_user
from supabase_api_config import api_config_service
from supabase_models import (
    LoginRequest, RegisterRequest, AuthResponse, 
    PasswordResetRequest, PasswordUpdateRequest, SupabaseUser
)
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["supabase-auth"])

@router.post("/register", response_model=AuthResponse)
async def register(register_data: RegisterRequest):
    """用户注册"""
    return await auth_service.register(register_data)

@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    """用户登录"""
    return await auth_service.login(login_data)

@router.post("/logout")
async def logout(current_user: SupabaseUser = Depends(get_current_user)):
    """用户登出"""
    return await auth_service.logout(current_user.id)

@router.get("/me", response_model=SupabaseUser)
async def get_current_user_info(current_user: SupabaseUser = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

@router.post("/refresh")
async def refresh_token(refresh_data: Dict[str, str]):
    """刷新访问令牌"""
    refresh_token = refresh_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少刷新令牌"
        )
    return await auth_service.refresh_token(refresh_token)

@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetRequest):
    """重置密码"""
    return await auth_service.reset_password(reset_data)

@router.post("/update-password")
async def update_password(
    password_data: PasswordUpdateRequest,
    current_user: SupabaseUser = Depends(get_current_user)
):
    """更新密码"""
    return await auth_service.update_password(current_user.id, password_data)

# API配置相关路由
@router.post("/api-config")
async def save_api_config(
    api_config: Dict[str, Any],
    current_user: SupabaseUser = Depends(get_current_user)
):
    """保存用户API配置"""
    try:
        result = await api_config_service.save_api_config(current_user, api_config)
        return {
            "message": "API配置保存成功",
            "config_id": result.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/api-config")
async def get_api_config(current_user: SupabaseUser = Depends(get_current_user)):
    """获取用户API配置"""
    config = await api_config_service.get_api_config(current_user)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到API配置"
        )
    return {"config": config}

@router.put("/api-config")
async def update_api_config(
    api_config: Dict[str, Any],
    current_user: SupabaseUser = Depends(get_current_user)
):
    """更新用户API配置"""
    try:
        result = await api_config_service.update_api_config(current_user, api_config)
        return {
            "message": "API配置更新成功",
            "config_id": result.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/api-config")
async def delete_api_config(current_user: SupabaseUser = Depends(get_current_user)):
    """删除用户API配置"""
    success = await api_config_service.delete_api_config(current_user)
    if success:
        return {"message": "API配置删除成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除API配置失败"
        )

@router.post("/api-config/test")
async def test_api_config(
    api_config: Dict[str, Any],
    current_user: SupabaseUser = Depends(get_current_user)
):
    """测试API配置"""
    return await api_config_service.test_api_config(current_user, api_config)
