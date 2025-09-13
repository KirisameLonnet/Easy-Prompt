"""
用户认证API路由
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from auth_models import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from user_database import get_user_database
from jwt_auth import create_user_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
from crypto_utils import get_crypto_manager

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate):
    """
    用户注册
    
    Args:
        user_create: 用户注册数据
        
    Returns:
        创建的用户信息
        
    Raises:
        HTTPException: 注册失败
    """
    try:
        user_db = get_user_database()
        user = user_db.create_user(user_create)
        return UserResponse(**user.dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """
    用户登录
    
    Args:
        user_login: 用户登录数据
        
    Returns:
        JWT令牌
        
    Raises:
        HTTPException: 登录失败
    """
    user_db = get_user_database()
    user = user_db.authenticate_user(user_login.username, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账户已被禁用"
        )
    
    access_token = create_user_token(user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        当前用户信息
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    更新当前用户信息
    
    Args:
        user_update: 用户更新数据
        current_user: 当前用户
        
    Returns:
        更新后的用户信息
        
    Raises:
        HTTPException: 更新失败
    """
    try:
        user_db = get_user_database()
        updated_user = user_db.update_user(current_user.id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(**updated_user.dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """
    用户登出
    
    Returns:
        登出成功消息
    """
    # JWT是无状态的，客户端删除令牌即可
    return {"message": "登出成功"}

@router.get("/verify-token")
async def verify_token(current_user: UserResponse = Depends(get_current_active_user)):
    """
    验证令牌有效性
    
    Args:
        current_user: 当前用户
        
    Returns:
        令牌有效信息
    """
    return {
        "valid": True,
        "user": current_user,
        "message": "令牌有效"
    }
