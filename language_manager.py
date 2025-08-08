import os
import json
import importlib
from pathlib import Path

class LanguageManager:
    """
    Manages all internationalization (i18n) aspects of the application.
    It loads static UI text and dynamic system prompts based on the
    EASYPROMPT_LANG environment variable.
    """
    def __init__(self, lang_code: str = None):
        self.lang_code = lang_code or os.getenv("EASYPROMPT_LANG", "zh")
        self.base_path = Path(__file__).parent / "locales" / self.lang_code
        
        self.static_text = self._load_static_text()
        self.system_prompts = self._load_system_prompts()

    def _load_static_text(self):
        """Loads the static text JSON file for the selected language."""
        file_path = self.base_path / "static_text.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Static text file not found for language '{self.lang_code}'")
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _load_system_prompts(self):
        """Dynamically imports the system prompts module for the selected language."""
        module_name = f"locales.{self.lang_code}.system_prompts"
        try:
            return importlib.import_module(module_name)
        except ImportError:
            raise FileNotFoundError(f"System prompts module not found for language '{self.lang_code}'")

    def t(self, key: str, **kwargs):
        """
        Retrieves a translated string by its key and formats it with provided arguments.
        e.g., t("SCORE_FEEDBACK", score=7, threshold=8)
        """
        return self.static_text.get(key, key).format(**kwargs)

# Create a default instance to be used across the application
# This ensures that the language is set once at startup.
lang_manager = LanguageManager()
