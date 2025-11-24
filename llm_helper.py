"""
Handles all interactions with LLM APIs, supporting both Google Generative AI
and OpenAI-compatible APIs (OpenAI, Claude, DeepSeek, etc.)
"""
import os
import json
from language_manager import lang_manager
from openai_helper import (
    init_openai_llm, is_openai_configured,
    get_openai_conversation_response_stream,
    evaluate_openai_profile,
    write_openai_final_prompt_stream,
    run_openai_structured_prompt
)
from gemini_helper import (
    init_gemini_llm, is_gemini_configured,
    get_gemini_conversation_response_stream,
    evaluate_gemini_profile,
    write_gemini_final_prompt_stream,
    start_gemini_chat_session,
    run_gemini_structured_prompt
)

# --- API Type Configuration ---
# 移除全局状态，改为每个连接独立的配置管理

def init_llm(nsfw_mode: bool = False, api_type: str = "openai", **kwargs):
    """
    Initializes LLM models based on API type and configuration.
    
    Args:
        nsfw_mode: Whether to enable NSFW mode
        api_type: "gemini" or "openai"
        **kwargs: Additional configuration (api_key, base_url, model, etc.)
    """
    # 不再使用全局状态，每次调用都重新初始化
    
    if api_type == "openai":
        # Initialize OpenAI-compatible API
        required_params = ["api_key", "base_url", "model"]
        for param in required_params:
            if param not in kwargs:
                print(f"错误: OpenAI API配置缺少参数: {param}")
                return False
        
        try:
            init_openai_llm(
                api_key=kwargs["api_key"],
                base_url=kwargs["base_url"],
                model=kwargs["model"],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4000),
                nsfw_mode=nsfw_mode
            )
            print(f"OpenAI兼容API已初始化: {kwargs['model']} (R18: {'开启' if nsfw_mode else '关闭'})")
            return True
        except Exception as e:
            print(f"OpenAI API初始化失败: {e}")
            return False
    
    elif api_type == "gemini":
        # Initialize Gemini API with frontend configuration
        required_params = ["api_key", "model"]
        for param in required_params:
            if param not in kwargs:
                print(f"错误: Gemini API配置缺少参数: {param}")
                return False
        
        try:
            init_gemini_llm(
                api_key=kwargs["api_key"],
                model=kwargs["model"],
                evaluator_model=kwargs.get("evaluator_model"),
                temperature=kwargs.get("temperature", 0.7),
                nsfw_mode=nsfw_mode
            )
            chat_session = None  # Reset chat session
            print(f"Gemini API已初始化: {kwargs['model']} (R18: {'开启' if nsfw_mode else '关闭'})")
            return True
        except Exception as e:
            print(f"Gemini API初始化失败: {e}")
            return False
    
    else:
        print(f"不支持的API类型: {api_type}")
        return False

def get_conversation_response_stream(chat_session, user_message: str, critique: str):
    """
    Gets a streaming response from the conversation model, guided by a critique.
    Supports both Gemini and OpenAI-compatible APIs.
    """
    # 检查当前配置的API类型
    from openai_helper import is_openai_configured
    from gemini_helper import is_gemini_configured
    
    if is_openai_configured():
        # For OpenAI, use chat history instead of session
        try:
            # 创建临时的聊天历史
            chat_history = []
            stream_gen = get_openai_conversation_response_stream(chat_history, user_message, critique)
            ai_response = ""
            trait = "None"
            
            for chunk in stream_gen:
                if isinstance(chunk, tuple) and len(chunk) == 3 and chunk[0] == "__FINAL_RESULT__":
                    # This is the final result tuple
                    _, ai_response, trait = chunk
                    break
                yield chunk
            
            yield ("__FINAL_RESULT__", ai_response, trait)
                
        except Exception as e:
            error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
            print(error_message)
            yield error_message
            yield ("__FINAL_RESULT__", error_message, "None")
    
    elif is_gemini_configured():
        try:
            stream_gen = get_gemini_conversation_response_stream(chat_session, user_message, critique)
            for chunk in stream_gen:
                yield chunk
                
        except Exception as e:
            error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
            print(error_message)
            yield error_message
            yield ("__FINAL_RESULT__", error_message, "None")
    
    else:
        error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
        yield error_msg
        yield ("__FINAL_RESULT__", error_msg, "None")

def evaluate_profile(full_profile: str) -> dict:
    """
    Gets a diagnostic report from the evaluator model.
    Supports both Gemini and OpenAI-compatible APIs.
    """
    from openai_helper import is_openai_configured
    from gemini_helper import is_gemini_configured
    
    if is_openai_configured():
        return evaluate_openai_profile(full_profile)
    
    elif is_gemini_configured():
        return evaluate_gemini_profile(full_profile)
    
    else:
        return {"is_ready_for_writing": False, "critique": lang_manager.t("ERROR_LLM_NOT_CONFIGURED")}

def write_final_prompt_stream(full_profile: str):
    """
    Gets the final, formatted System Prompt from the writer model as a stream.
    Supports both Gemini and OpenAI-compatible APIs.
    """
    from openai_helper import is_openai_configured
    from gemini_helper import is_gemini_configured
    
    if is_openai_configured():
        for chunk in write_openai_final_prompt_stream(full_profile):
            yield chunk
        return
    
    elif is_gemini_configured():
        for chunk in write_gemini_final_prompt_stream(full_profile):
            yield chunk
        return
    
    else:
        yield lang_manager.t("ERROR_LLM_NOT_CONFIGURED")

def start_chat_session():
    """Starts a new chat session with the conversation model."""
    from openai_helper import is_openai_configured
    from gemini_helper import is_gemini_configured, start_gemini_chat_session
    
    if is_openai_configured():
        # Return a placeholder for OpenAI
        return "openai_session"
    
    elif is_gemini_configured():
        # Start Gemini chat session
        return start_gemini_chat_session()
    
    else:
        return None

def get_current_api_type() -> str:
    """Get current API type - 返回最后配置的API类型"""
    from openai_helper import is_openai_configured, openai_config
    from gemini_helper import is_gemini_configured, gemini_config
    
    # 检查哪个API已配置
    openai_configured = is_openai_configured() and openai_config.get("api_key") and openai_config.get("base_url") and openai_config.get("model")
    gemini_configured = is_gemini_configured() and gemini_config.get("api_key") and gemini_config.get("model")
    
    # 如果两个都配置了，返回最后配置的（通过检查配置的完整性）
    if openai_configured and gemini_configured:
        # 检查哪个配置更完整，优先返回Gemini（因为它是后配置的）
        return "gemini"
    elif openai_configured:
        return "openai"
    elif gemini_configured:
        return "gemini"
    else:
        return "none"

def reset_chat_history():
    """Reset chat history for OpenAI sessions - 不再需要，因为不再使用全局状态"""
    pass

def run_structured_prompt(system_prompt: str, user_prompt: str) -> str:
    """Run a lightweight structured prompt with whichever API is configured."""
    api_type = get_current_api_type()
    if api_type == "openai":
        return run_openai_structured_prompt(system_prompt, user_prompt)
    if api_type == "gemini":
        return run_gemini_structured_prompt(system_prompt, user_prompt)
    raise ValueError("LLM未配置，无法运行结构化提示")