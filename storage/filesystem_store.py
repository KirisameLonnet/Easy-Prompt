"""
Filesystem-based Session Storage Implementation
基于文件系统的会话存储实现
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from storage.session_store import SessionStore
from schemas import Session


class FileSystemSessionStore(SessionStore):
    """
    基于文件系统的会话存储
    
    目录结构：
    - sessions/anonymous/        # 匿名用户（未登录）
    - sessions/users/{user_id}/  # 注册用户
    """
    
    def __init__(self, base_path: str = "./sessions"):
        """
        初始化文件系统存储
        
        Args:
            base_path: 基础存储路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # 创建匿名用户目录
        self.anonymous_dir = self.base_path / "anonymous"
        self.anonymous_dir.mkdir(exist_ok=True)
        
        # 用户目录
        self.users_dir = self.base_path / "users"
        self.users_dir.mkdir(exist_ok=True)
    
    def _get_user_dir(self, user_id: Optional[str] = None) -> Path:
        """
        获取用户目录
        
        Args:
            user_id: 用户ID，None表示匿名用户
            
        Returns:
            用户目录路径
        """
        if user_id is None or user_id == "anonymous":
            return self.anonymous_dir
        else:
            user_dir = self.users_dir / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir
    
    def get_session_path(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> Path:
        """获取会话目录路径"""
        return self._get_user_dir(user_id) / session_id
    
    async def create_session(
        self, 
        session: Session, 
        user_id: Optional[str] = None
    ) -> Session:
        """创建新会话"""
        session_dir = self.get_session_path(session.id, user_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存会话元数据
        session_file = session_dir / "session.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.dict(), f, ensure_ascii=False, indent=2, default=str)
        
        # 初始化角色档案文件
        profile_file = session_dir / "character_profile.txt"
        if not profile_file.exists():
            profile_file.touch()
        
        return session
    
    async def get_session(
        self, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> Optional[Session]:
        """获取指定会话"""
        session_file = self.get_session_path(session_id, user_id) / "session.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                session = Session(**data)
                
                # 验证用户权限
                if user_id and session.user_id and session.user_id != user_id:
                    return None
                
                return session
        except Exception as e:
            print(f"加载会话失败 {session_id}: {e}")
            return None
    
    async def list_sessions(
        self, 
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Session]:
        """列出会话"""
        user_dir = self._get_user_dir(user_id)
        sessions = []
        
        if not user_dir.exists():
            return sessions
        
        # 遍历所有会话目录
        session_dirs = [d for d in user_dir.iterdir() if d.is_dir()]
        
        # 按修改时间排序（最新的在前）
        session_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 分页
        session_dirs = session_dirs[offset:offset + limit]
        
        for session_dir in session_dirs:
            session_file = session_dir / "session.json"
            if session_file.exists():
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        sessions.append(Session(**data))
                except Exception as e:
                    print(f"加载会话失败 {session_dir.name}: {e}")
                    continue
        
        return sessions
    
    async def update_session(
        self, 
        session: Session, 
        user_id: Optional[str] = None
    ) -> Session:
        """更新会话"""
        # 验证权限
        existing = await self.get_session(session.id, user_id)
        if not existing:
            raise ValueError(f"Session {session.id} not found or no permission")
        
        # 更新时间戳
        session.updated_at = datetime.now()
        
        # 保存
        session_file = self.get_session_path(session.id, user_id) / "session.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.dict(), f, ensure_ascii=False, indent=2, default=str)
        
        return session
    
    async def delete_session(
        self, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> bool:
        """删除会话"""
        session_dir = self.get_session_path(session_id, user_id)
        
        if not session_dir.exists():
            return False
        
        try:
            shutil.rmtree(session_dir)
            return True
        except Exception as e:
            print(f"删除会话失败 {session_id}: {e}")
            return False
    
    async def save_profile(
        self, 
        session_id: str, 
        profile_content: str,
        user_id: Optional[str] = None
    ):
        """保存角色档案内容"""
        profile_file = self.get_session_path(session_id, user_id) / "character_profile.txt"
        profile_file.write_text(profile_content, encoding='utf-8')
    
    async def load_profile(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """加载角色档案内容"""
        profile_file = self.get_session_path(session_id, user_id) / "character_profile.txt"
        
        if not profile_file.exists():
            return ""
        
        return profile_file.read_text(encoding='utf-8')
    
    async def append_to_profile(
        self, 
        session_id: str, 
        content: str,
        user_id: Optional[str] = None
    ):
        """追加内容到角色档案"""
        profile_file = self.get_session_path(session_id, user_id) / "character_profile.txt"
        
        with open(profile_file, 'a', encoding='utf-8') as f:
            f.write(content + "\n")
    
    async def save_final_prompt(
        self, 
        session_id: str, 
        prompt_content: str,
        user_id: Optional[str] = None
    ):
        """保存最终生成的提示词"""
        prompt_file = self.get_session_path(session_id, user_id) / "final_prompt.md"
        prompt_file.write_text(prompt_content, encoding='utf-8')
    
    async def load_final_prompt(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """加载最终提示词"""
        prompt_file = self.get_session_path(session_id, user_id) / "final_prompt.md"
        
        if not prompt_file.exists():
            return None
        
        return prompt_file.read_text(encoding='utf-8')

