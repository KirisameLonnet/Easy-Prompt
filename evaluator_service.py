import time
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import llm_helper
from language_manager import lang_manager

class ProfileChangeHandler(FileSystemEventHandler):
    """
    Handles file system events for 'character_profile.txt' files.
    """
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("character_profile.txt"):
            # print(lang_manager.t("EVALUATOR_DETECTED_CHANGE", path=event.src_path))
            self.process_profile(Path(event.src_path))

    def process_profile(self, profile_path: Path):
        """
        Reads the profile, calls the evaluator LLM, and writes the score.
        """
        score_file = profile_path.parent / "score.json"
        full_profile = profile_path.read_text(encoding="utf-8")

        if not full_profile.strip():
            # print(lang_manager.t("EVALUATOR_EMPTY_PROFILE"))
            return

        # print(lang_manager.t("EVALUATOR_EVALUATING"))
        evaluation_data = llm_helper.evaluate_profile(full_profile)
        
        if evaluation_data and "critique" in evaluation_data:
            # print(lang_manager.t("EVALUATOR_SCORE_RECEIVED", score=evaluation_data.get('score')))
            with open(score_file, "w", encoding="utf-8") as f:
                json.dump(evaluation_data, f, ensure_ascii=False, indent=4)
        else:
            # print(lang_manager.t("EVALUATOR_SCORE_FAILED"))
            pass


class EvaluatorService:
    """
    A background service that monitors the 'sessions' directory for changes.
    """
    def __init__(self, path: str = './sessions'):
        self.path = path
        self.event_handler = ProfileChangeHandler()
        self.observer = Observer()

    def start(self):
        """Starts the file system observer in a separate thread."""
        Path(self.path).mkdir(exist_ok=True)
        
        self.observer.schedule(self.event_handler, self.path, recursive=True)
        self.observer.start()
        print(lang_manager.t("EVALUATOR_SERVICE_START", path=self.path))

    def stop(self):
        """Stops the observer."""
        self.observer.stop()
        self.observer.join()
        print(lang_manager.t("EVALUATOR_SERVICE_STOP"))
