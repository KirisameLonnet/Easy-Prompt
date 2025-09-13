"""
用户配置管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from auth_models import UserResponse
from user_database import get_user_database
from jwt_auth import get_current_active_user
from llm_helper import init_llm

router = APIRouter(prefix="/user", tags=["user-config"])

@router.post("/api-config")
async def save_api_config(
    api_config: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    保存用户API配置
    
    Args:
        api_config: API配置数据
        current_user: 当前用户
        
    Returns:
        保存成功消息
        
    Raises:
        HTTPException: 保存失败
    """
    try:
        user_db = get_user_database()
        
        # 验证API配置
        if not _validate_api_config(api_config):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API配置不完整或格式错误"
            )
        
        # 保存配置
        user_db.save_api_config(current_user.id, api_config)
        
        return {
            "message": "API配置保存成功",
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存API配置失败: {str(e)}"
        )

@router.get("/api-config")
async def get_api_config(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    获取用户API配置
    
    Args:
        current_user: 当前用户
        
    Returns:
        用户的API配置
    """
    try:
        user_db = get_user_database()
        api_config = user_db.get_user_api_config(current_user.id)
        
        if not api_config:
            return {
                "message": "未找到API配置",
                "config": None
            }
        
        # 不返回API密钥，只返回其他配置
        safe_config = {k: v for k, v in api_config.items() if k != "api_key"}
        
        return {
            "message": "API配置获取成功",
            "config": safe_config,
            "has_api_key": bool(api_config.get("api_key"))
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取API配置失败: {str(e)}"
        )

@router.put("/api-config")
async def update_api_config(
    api_config: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    更新用户API配置
    
    Args:
        api_config: 新的API配置数据
        current_user: 当前用户
        
    Returns:
        更新成功消息
        
    Raises:
        HTTPException: 更新失败
    """
    try:
        user_db = get_user_database()
        
        # 验证API配置
        if not _validate_api_config(api_config):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API配置不完整或格式错误"
            )
        
        # 更新配置
        user_db.update_user_api_config(current_user.id, api_config)
        
        return {
            "message": "API配置更新成功",
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新API配置失败: {str(e)}"
        )

@router.delete("/api-config")
async def delete_api_config(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    删除用户API配置
    
    Args:
        current_user: 当前用户
        
    Returns:
        删除成功消息
    """
    try:
        user_db = get_user_database()
        success = user_db.delete_user_api_configs(current_user.id)
        
        if success:
            return {
                "message": "API配置删除成功",
                "user_id": current_user.id
            }
        else:
            return {
                "message": "未找到API配置",
                "user_id": current_user.id
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除API配置失败: {str(e)}"
        )

@router.post("/test-api-config")
async def test_api_config(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    测试用户API配置
    
    Args:
        current_user: 当前用户
        
    Returns:
        测试结果
    """
    try:
        user_db = get_user_database()
        api_config = user_db.get_user_api_config(current_user.id)
        
        if not api_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到API配置"
            )
        
        # 测试API配置
        success = init_llm(
            nsfw_mode=api_config.get("nsfw_mode", False),
            api_type=api_config.get("api_type", "openai"),
            **{k: v for k, v in api_config.items() if k != "nsfw_mode" and k != "api_type"}
        )
        
        if success:
            return {
                "message": "API配置测试成功",
                "api_type": api_config.get("api_type"),
                "model": api_config.get("model"),
                "base_url": api_config.get("base_url", "N/A")
            }
        else:
            return {
                "message": "API配置测试失败",
                "error": "无法初始化API"
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试API配置失败: {str(e)}"
        )

def _validate_api_config(api_config: Dict[str, Any]) -> bool:
    """
    验证API配置
    
    Args:
        api_config: API配置数据
        
    Returns:
        配置是否有效
    """
    if not api_config:
        return False
    
    api_type = api_config.get("api_type")
    
    if api_type == "openai":
        required_fields = ["api_key", "base_url", "model"]
        return all(api_config.get(field) for field in required_fields)
    elif api_type == "gemini":
        required_fields = ["api_key", "model"]
        return all(api_config.get(field) for field in required_fields)
    else:
        return False
