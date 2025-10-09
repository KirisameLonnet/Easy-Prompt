"""
Session Storage Abstract Interface
会话存储抽象接口 - 为未来多存储后端支持做准备
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from pathlib import Path

from schemas import Session, ChatMessage, EvaluationData


class SessionStore(ABC):
    """
    会话存储抽象接口
    
    定义了会话数据的CRUD操作，支持用户隔离。
    具体实现可以是文件系统、数据库、云存储等。
    """
    
    @abstractmethod
    async def create_session(
        self, 
        session: Session, 
        user_id: Optional[str] = None
    ) -> Session:
        """
        创建新会话
        
        Args:
            session: 会话对象
            user_id: 用户ID（可选，None表示匿名用户）
            
        Returns:
            创建的会话对象
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def list_sessions(
        self, 
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Session]:
        """
        列出会话
        
        Args:
            user_id: 用户ID（None表示列出匿名会话）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    async def update_session(
        self, 
        session: Session, 
        user_id: Optional[str] = None
    ) -> Session:
        """
        更新会话
        
        Args:
            session: 会话对象
            user_id: 用户ID（用于权限验证）
            
        Returns:
            更新后的会话对象
        """
        pass
    
    @abstractmethod
    async def delete_session(
        self, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    async def save_profile(
        self, 
        session_id: str, 
        profile_content: str,
        user_id: Optional[str] = None
    ):
        """
        保存角色档案内容
        
        Args:
            session_id: 会话ID
            profile_content: 角色档案内容
            user_id: 用户ID
        """
        pass
    
    @abstractmethod
    async def load_profile(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        加载角色档案内容
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            角色档案内容
        """
        pass
    
    @abstractmethod
    async def append_to_profile(
        self, 
        session_id: str, 
        content: str,
        user_id: Optional[str] = None
    ):
        """
        追加内容到角色档案
        
        Args:
            session_id: 会话ID
            content: 要追加的内容
            user_id: 用户ID
        """
        pass
    
    @abstractmethod
    async def save_final_prompt(
        self, 
        session_id: str, 
        prompt_content: str,
        user_id: Optional[str] = None
    ):
        """
        保存最终生成的提示词
        
        Args:
            session_id: 会话ID
            prompt_content: 提示词内容
            user_id: 用户ID
        """
        pass
    
    @abstractmethod
    async def load_final_prompt(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        加载最终提示词
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            提示词内容，不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_session_path(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> Path:
        """
        获取会话存储路径（用于文件系统实现）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            会话路径
        """
        pass

