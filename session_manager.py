"""
Session Manager - 统一的会话管理接口
支持用户隔离，为未来的多用户系统做准备
"""
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import Depends, HTTPException

from schemas import Session, SessionStatus, ChatMessage, EvaluationData
from conversation_handler import ConversationHandler
from storage import SessionStore, FileSystemSessionStore


class SessionManager:
    """
    会话管理器
    
    提供会话的生命周期管理，支持用户隔离。
    通过依赖注入的存储层，可以轻松切换不同的存储后端。
    """
    
    def __init__(self, store: SessionStore):
        """
        初始化会话管理器
        
        Args:
            store: 会话存储实现
        """
        self.store = store
        self.active_handlers: Dict[str, ConversationHandler] = {}
    
    async def create_session(
        self, 
        user_id: Optional[str] = None,
        name: Optional[str] = None, 
        **kwargs
    ) -> Session:
        """
        创建新会话
        
        Args:
            user_id: 用户ID（None表示匿名用户）
            name: 会话名称
            **kwargs: 其他参数
            
        Returns:
            创建的会话对象
        """
        session_id = str(uuid.uuid4())
        
        if not name:
            now = datetime.now()
            name = f"会话 {now.strftime('%Y-%m-%d %H:%M')}"
        
        # 创建会话对象
        session = Session(
            id=session_id,
            name=name,
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE
        )
        
        # 通过存储层创建
        session = await self.store.create_session(session, user_id)
        
        # 创建对话处理器
        handler = ConversationHandler(session_id=session_id, user_id=user_id)
        self.active_handlers[session_id] = handler
        
        return session
    
    async def get_session(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Session]:
        """
        获取指定会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            会话对象，不存在或无权限则返回None
        """
        return await self.store.get_session(session_id, user_id)
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Session]:
        """
        列出会话
        
        Args:
            user_id: 用户ID（None表示匿名用户）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            会话列表
        """
        return await self.store.list_sessions(user_id, limit, offset)

    async def get_all_sessions(self) -> List[Session]:
        """向后兼容的别名，用于REST路由"""
        return await self.store.list_sessions(user_id=None, limit=200, offset=0)
    
    async def update_session(
        self, 
        session_id: str,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> Optional[Session]:
        """
        更新会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            name: 新名称
            status: 新状态
            
        Returns:
            更新后的会话对象
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            return None
        
        if name is not None:
            session.name = name
        if status is not None:
            session.status = status
        
        session.updated_at = datetime.now()
        return await self.store.update_session(session, user_id)
    
    async def delete_session(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            是否成功删除
        """
        # 清理内存中的handler
        self.active_handlers.pop(session_id, None)
        
        # 通过存储层删除
        return await self.store.delete_session(session_id, user_id)
    
    async def add_message_to_session(
        self, 
        session_id: str, 
        message: ChatMessage,
        user_id: Optional[str] = None
    ) -> Optional[Session]:
        """
        向会话添加消息
        
        Args:
            session_id: 会话ID
            message: 消息对象
            user_id: 用户ID
            
        Returns:
            更新后的会话对象
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            return None
        
        session.messages.append(message)
        session.message_count = len(session.messages)
        session.last_message = message.content
        session.updated_at = datetime.now()
        
        return await self.store.update_session(session, user_id)
    
    async def update_evaluation_data(
        self, 
        session_id: str, 
        evaluation_data: EvaluationData,
        user_id: Optional[str] = None
    ) -> Optional[Session]:
        """
        更新会话的评估数据
        
        Args:
            session_id: 会话ID
            evaluation_data: 评估数据
            user_id: 用户ID
            
        Returns:
            更新后的会话对象
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            return None
        
        session.evaluation_data = evaluation_data
        session.updated_at = datetime.now()
        
        return await self.store.update_session(session, user_id)
    
    def get_handler(self, session_id: str) -> Optional[ConversationHandler]:
        """
        获取会话的对话处理器
        
        Args:
            session_id: 会话ID
            
        Returns:
            对话处理器对象
        """
        return self.active_handlers.get(session_id)
    
    def create_handler(self, session_id: str, user_id: Optional[str] = None) -> ConversationHandler:
        """
        为会话创建对话处理器
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            对话处理器对象
        """
        handler = ConversationHandler(session_id=session_id, user_id=user_id)
        self.active_handlers[session_id] = handler
        return handler
    
    def remove_handler(self, session_id: str):
        """
        移除会话的对话处理器
        
        Args:
            session_id: 会话ID
        """
        self.active_handlers.pop(session_id, None)
    
    def get_session_path(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ):
        """
        获取会话存储路径（用于ProfileManager兼容）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            会话路径
        """
        return self.store.get_session_path(session_id, user_id)


# 创建默认的会话管理器实例（使用文件系统存储）
_default_store = FileSystemSessionStore(base_path="./sessions")
session_manager = SessionManager(store=_default_store)


# 依赖注入函数（兼容旧的session_service接口）
async def get_session_service() -> SessionManager:
    """获取会话管理器依赖（兼容旧接口）"""
    return session_manager


async def get_session_manager() -> SessionManager:
    """获取会话管理器依赖"""
    return session_manager


async def get_session(
    session_id: str, 
    manager: SessionManager = Depends(get_session_manager),
    user_id: Optional[str] = None
) -> Session:
    """
    获取会话依赖
    
    Args:
        session_id: 会话ID
        manager: 会话管理器
        user_id: 用户ID
        
    Returns:
        会话对象
    """
    session = await manager.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session
