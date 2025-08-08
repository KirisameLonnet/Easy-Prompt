import os
import uuid
import json
from pathlib import Path

class ProfileManager:
    """
    Manages the file-based storage for a single character profile session.
    """
    def __init__(self, base_path: str = "./sessions"):
        self.session_id = str(uuid.uuid4())
        self.session_path = Path(base_path) / self.session_id
        self.profile_file = self.session_path / "character_profile.txt"
        self.evaluation_file = self.session_path / "evaluation.json"
        self.final_prompt_file = self.session_path / "final_prompt.md"
        
        self.session_path.mkdir(parents=True, exist_ok=True)

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
