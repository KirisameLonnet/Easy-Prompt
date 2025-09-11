"""
FastAPI Session Management Service
符合FastAPI规范的会话管理服务
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from fastapi import Depends, HTTPException
from contextlib import asynccontextmanager

from schemas import Session, SessionStatus, ChatMessage, EvaluationData, ApiConfig
from conversation_handler import ConversationHandler
from profile_manager import ProfileManager


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.active_handlers: Dict[str, ConversationHandler] = {}
        self.sessions_dir = Path("./sessions")
        self.sessions_dir.mkdir(exist_ok=True)
    
    async def create_session(
        self, 
        name: Optional[str] = None, 
        api_config: Optional[ApiConfig] = None
    ) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        
        if not name:
            now = datetime.now()
            name = f"会话 {now.strftime('%Y-%m-%d %H:%M')}"
        
        # 创建会话对象
        session = Session(
            id=session_id,
            name=name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE
        )
        
        # 创建对话处理器
        handler = ConversationHandler(session_id=session_id)
        self.active_handlers[session_id] = handler
        self.sessions[session_id] = session
        
        # 保存会话到文件
        await self._save_session_to_file(session)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取指定会话"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # 尝试从文件加载
        session = await self._load_session_from_file(session_id)
        if session:
            self.sessions[session_id] = session
            return session
        
        return None
    
    async def get_all_sessions(self) -> List[Session]:
        """获取所有会话"""
        # 首先加载所有文件中的会话
        await self._load_all_sessions_from_files()
        return list(self.sessions.values())
    
    async def update_session(
        self, 
        session_id: str, 
        name: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> Optional[Session]:
        """更新会话"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        if name is not None:
            session.name = name
        if status is not None:
            session.status = status
        
        session.updated_at = datetime.now()
        await self._save_session_to_file(session)
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        # 清理内存中的会话
        session = self.sessions.pop(session_id, None)
        handler = self.active_handlers.pop(session_id, None)
        
        if session:
            # 删除文件
            session_file = self.sessions_dir / session_id / "session.json"
            if session_file.exists():
                session_file.unlink()
            
            # 删除整个会话目录
            session_dir = self.sessions_dir / session_id
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)
            
            return True
        
        return False
    
    async def add_message_to_session(
        self, 
        session_id: str, 
        message: ChatMessage
    ) -> Optional[Session]:
        """向会话添加消息"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.messages.append(message)
        session.message_count = len(session.messages)
        session.last_message = message.content
        session.updated_at = datetime.now()
        
        await self._save_session_to_file(session)
        return session
    
    async def update_evaluation_data(
        self, 
        session_id: str, 
        evaluation_data: EvaluationData
    ) -> Optional[Session]:
        """更新会话的评估数据"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.evaluation_data = evaluation_data
        session.updated_at = datetime.now()
        
        await self._save_session_to_file(session)
        return session
    
    def get_handler(self, session_id: str) -> Optional[ConversationHandler]:
        """获取会话的对话处理器"""
        return self.active_handlers.get(session_id)
    
    def create_handler(self, session_id: str) -> ConversationHandler:
        """为会话创建对话处理器"""
        handler = ConversationHandler(session_id=session_id)
        self.active_handlers[session_id] = handler
        return handler
    
    def remove_handler(self, session_id: str):
        """移除会话的对话处理器"""
        self.active_handlers.pop(session_id, None)
    
    async def _save_session_to_file(self, session: Session):
        """保存会话到文件"""
        session_dir = self.sessions_dir / session.id
        session_dir.mkdir(exist_ok=True)
        
        session_file = session_dir / "session.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.dict(), f, ensure_ascii=False, indent=2, default=str)
    
    async def _load_session_from_file(self, session_id: str) -> Optional[Session]:
        """从文件加载会话"""
        session_file = self.sessions_dir / session_id / "session.json"
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Session(**data)
        except Exception as e:
            print(f"加载会话文件失败 {session_id}: {e}")
            return None
    
    async def _load_all_sessions_from_files(self):
        """从文件加载所有会话"""
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                session_id = session_dir.name
                if session_id not in self.sessions:
                    session = await self._load_session_from_file(session_id)
                    if session:
                        self.sessions[session_id] = session


# 全局会话服务实例
session_service = SessionService()


# 依赖注入函数
async def get_session_service() -> SessionService:
    """获取会话服务依赖"""
    return session_service


async def get_session(session_id: str, service: SessionService = Depends(get_session_service)) -> Session:
    """获取会话依赖"""
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session
