"""
Session Management REST API Routes
会话管理REST API路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from schemas import (
    Session, SessionCreate, SessionUpdate, SessionResponse, 
    SessionStatus, ChatMessage, EvaluationData
)
from session_service import SessionService, get_session_service, get_session

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    service: SessionService = Depends(get_session_service)
):
    """创建新会话"""
    try:
        session = await service.create_session(
            name=session_data.name,
            api_config=session_data.api_config
        )
        return SessionResponse(
            success=True,
            message="会话创建成功",
            data=session
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败: {str(e)}"
        )


@router.get("/", response_model=SessionResponse)
async def get_all_sessions(
    service: SessionService = Depends(get_session_service)
):
    """获取所有会话"""
    try:
        sessions = await service.get_all_sessions()
        return SessionResponse(
            success=True,
            message=f"成功获取 {len(sessions)} 个会话",
            data=sessions
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_by_id(
    session: Session = Depends(get_session)
):
    """根据ID获取会话"""
    return SessionResponse(
        success=True,
        message="获取会话成功",
        data=session
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    service: SessionService = Depends(get_session_service)
):
    """更新会话"""
    try:
        session = await service.update_session(
            session_id=session_id,
            name=session_data.name,
            status=session_data.status
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return SessionResponse(
            success=True,
            message="会话更新成功",
            data=session
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新会话失败: {str(e)}"
        )


@router.delete("/{session_id}", response_model=SessionResponse)
async def delete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """删除会话"""
    try:
        success = await service.delete_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return SessionResponse(
            success=True,
            message="会话删除成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )


@router.post("/{session_id}/messages", response_model=SessionResponse)
async def add_message_to_session(
    session_id: str,
    message: ChatMessage,
    service: SessionService = Depends(get_session_service)
):
    """向会话添加消息"""
    try:
        session = await service.add_message_to_session(session_id, message)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return SessionResponse(
            success=True,
            message="消息添加成功",
            data=session
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加消息失败: {str(e)}"
        )


@router.put("/{session_id}/evaluation", response_model=SessionResponse)
async def update_session_evaluation(
    session_id: str,
    evaluation_data: EvaluationData,
    service: SessionService = Depends(get_session_service)
):
    """更新会话评估数据"""
    try:
        session = await service.update_evaluation_data(session_id, evaluation_data)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return SessionResponse(
            success=True,
            message="评估数据更新成功",
            data=session
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新评估数据失败: {str(e)}"
        )


@router.get("/{session_id}/messages", response_model=SessionResponse)
async def get_session_messages(
    session: Session = Depends(get_session)
):
    """获取会话的所有消息"""
    return SessionResponse(
        success=True,
        message=f"成功获取 {len(session.messages)} 条消息",
        data=session.messages
    )


@router.get("/{session_id}/evaluation", response_model=SessionResponse)
async def get_session_evaluation(
    session: Session = Depends(get_session)
):
    """获取会话的评估数据"""
    return SessionResponse(
        success=True,
        message="获取评估数据成功",
        data=session.evaluation_data
    )
