"""
Per-session Gemini API manager to avoid user conflicts
每个会话独立的Gemini API管理器，避免用户冲突
"""
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import Dict, Generator, Optional
from language_manager import lang_manager

class GeminiSession:
    """独立的Gemini会话，避免全局状态冲突"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.config = {
            "api_key": None,
            "model": "gemini-2.5-flash",
            "evaluator_model": "gemini-2.5-flash",
            "temperature": 0.7,
            "nsfw_mode": False
        }
        self.conversation_model = None
        self.evaluator_model = None
        self.writer_model = None
        self.chat_session = None
    
    def init_api(self, api_key: str, model: str = "gemini-2.5-flash", 
                 evaluator_model: str = None, temperature: float = 0.7, 
                 nsfw_mode: bool = False) -> bool:
        """初始化该会话的Gemini API配置"""
        try:
            if not evaluator_model:
                evaluator_model = model
            
            self.config.update({
                "api_key": api_key,
                "model": model,
                "evaluator_model": evaluator_model,
                "temperature": temperature,
                "nsfw_mode": nsfw_mode
            })
            
            # 为这个会话创建独立的API客户端
            # 注意：这里仍然会有全局配置冲突的问题
            # 理想情况下需要为每个会话创建独立的genai客户端实例
            genai.configure(api_key=api_key)
            
            # 创建安全设置
            safety_settings = None
            if nsfw_mode:
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            
            # 获取系统提示词
            prompts = lang_manager.system_prompts
            conversation_prompt = prompts.get_conversation_system_prompt(nsfw_mode)
            evaluator_prompt = prompts.get_evaluator_system_prompt(nsfw_mode)
            writer_prompt = prompts.get_writer_system_prompt(nsfw_mode)
            
            # 创建该会话专用的模型实例
            self.conversation_model = genai.GenerativeModel(
                model,
                system_instruction=conversation_prompt,
                safety_settings=safety_settings
            )
            
            self.evaluator_model = genai.GenerativeModel(
                evaluator_model,
                system_instruction=evaluator_prompt,
                safety_settings=safety_settings
            )
            
            self.writer_model = genai.GenerativeModel(
                model,
                system_instruction=writer_prompt,
                safety_settings=safety_settings,
                generation_config={"temperature": temperature}
            )
            
            print(f"会话 {self.session_id}: Gemini API已配置: {model} (评估: {evaluator_model}) (R18: {'开启' if nsfw_mode else '关闭'})")
            return True
            
        except Exception as e:
            print(f"会话 {self.session_id}: Gemini API初始化失败: {e}")
            return False
    
    def is_configured(self) -> bool:
        """检查该会话的Gemini配置是否完整"""
        return all([
            self.config["api_key"],
            self.config["model"],
            self.conversation_model is not None
        ])
    
    def start_chat_session(self):
        """为该会话启动聊天"""
        if self.conversation_model:
            self.chat_session = self.conversation_model.start_chat()
            return self.chat_session
        return None

# 全局会话管理器
class GeminiSessionManager:
    """管理所有Gemini会话的管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, GeminiSession] = {}
    
    def create_session(self, session_id: str) -> GeminiSession:
        """创建新的Gemini会话"""
        session = GeminiSession(session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[GeminiSession]:
        """获取指定的Gemini会话"""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """移除指定的Gemini会话"""
        self.sessions.pop(session_id, None)
    
    def cleanup_sessions(self):
        """清理所有会话"""
        self.sessions.clear()

# 全局实例
gemini_session_manager = GeminiSessionManager()
