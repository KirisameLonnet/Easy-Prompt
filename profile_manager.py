import os
import uuid
import json
from pathlib import Path
from typing import Optional

class ProfileManager:
    """
    Manages the file-based storage for a single character profile session.
    使用 SessionStore 抽象层进行文件操作，支持用户隔离。
    """
    def __init__(
        self, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_store: Optional['SessionStore'] = None
    ):
        """
        初始化 ProfileManager
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（用于用户隔离）
            session_store: SessionStore 实例（如果不提供则使用默认的）
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        
        # 使用 SessionStore 获取路径
        if session_store is None:
            from storage import default_store
            session_store = default_store
        
        self.store = session_store
        self.session_path = self.store.get_session_path(self.session_id, self.user_id)
        
        self.profile_file = self.session_path / "character_profile.txt"
        self.evaluation_file = self.session_path / "evaluation.json"
        self.final_prompt_file = self.session_path / "final_prompt.md"
        self.session_metadata_file = self.session_path / "session_metadata.json"
        
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # 如果是新session，初始化元数据
        if not self.session_metadata_file.exists():
            self.save_session_metadata()

    def append_trait(self, trait: str):
        """Appends a new trait to the character profile file."""
        with open(self.profile_file, "a", encoding="utf-8") as f:
            f.write(trait + "\n")

    def get_full_profile(self) -> str:
        """Reads the entire character profile."""
        if not self.profile_file.exists():
            return ""
        return self.profile_file.read_text(encoding="utf-8")

    def get_latest_evaluation(self) -> dict:
        """
        Reads the latest evaluation report from the json file.
        """
        if not self.evaluation_file.exists():
            return {"is_ready_for_writing": False, "critique": "档案为空，请开始描述。"}
        try:
            return json.loads(self.evaluation_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, TypeError):
            return {"is_ready_for_writing": False, "critique": "无法读取评估报告。"}

    def save_final_prompt(self, prompt_content: str):
        """Saves the final generated prompt to a file."""
        self.final_prompt_file.write_text(prompt_content, encoding="utf-8")
        print(f"\n[Info] Final prompt saved to: {self.final_prompt_file.resolve()}")

    def save_session_metadata(self, metadata: dict = None):
        """Saves session metadata to a JSON file."""
        if metadata is None:
            metadata = {
                "session_id": self.session_id,
                "created_at": self.get_current_timestamp(),
                "last_updated": self.get_current_timestamp(),
                "api_type": "unknown",
                "api_config": {},
                "chat_messages": [],
                "evaluation_data": {}
            }
        
        with open(self.session_metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def load_session_metadata(self) -> dict:
        """Loads session metadata from JSON file."""
        if not self.session_metadata_file.exists():
            return {}
        
        try:
            with open(self.session_metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def update_session_metadata(self, updates: dict):
        """Updates specific fields in session metadata."""
        metadata = self.load_session_metadata()
        metadata.update(updates)
        metadata["last_updated"] = self.get_current_timestamp()
        self.save_session_metadata(metadata)

    def get_current_timestamp(self) -> str:
        """Gets current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()

    @classmethod
    def find_existing_session(
        cls, 
        base_path: str = "./sessions",
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Finds the most recently updated session ID.
        
        Args:
            base_path: 基础路径
            user_id: 用户ID（用于用户隔离）
            
        Returns:
            最新的会话ID，如果没有则返回None
        """
        # 确定用户目录
        if user_id is None or user_id == "anonymous":
            user_dir = Path(base_path) / "anonymous"
        else:
            user_dir = Path(base_path) / "users" / user_id
        
        if not user_dir.exists():
            return None
        
        latest_session = None
        latest_time = 0
        
        for session_dir in user_dir.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / "session_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                            last_updated = metadata.get("last_updated", "")
                            if last_updated:
                                # 简单的字符串比较，实际项目中应该使用datetime
                                if last_updated > str(latest_time):
                                    latest_time = last_updated
                                    latest_session = session_dir.name
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return latest_session
