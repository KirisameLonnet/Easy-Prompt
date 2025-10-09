"""
Storage module for session management
会话存储模块
"""
from storage.session_store import SessionStore
from storage.filesystem_store import FileSystemSessionStore

# 创建默认的存储实例
default_store = FileSystemSessionStore(base_path="./sessions")

__all__ = ['SessionStore', 'FileSystemSessionStore', 'default_store']

