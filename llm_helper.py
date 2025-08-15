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
    write_openai_final_prompt_stream
)
from gemini_helper import (
    init_gemini_llm, is_gemini_configured,
    get_gemini_conversation_response_stream,
    evaluate_gemini_profile,
    write_gemini_final_prompt_stream,
    start_gemini_chat_session
)

# --- API Type Configuration ---
current_api_type = "openai"  # "gemini" or "openai" - 默认使用OpenAI兼容
chat_history = []  # For OpenAI-style chat history
chat_session = None  # For Gemini chat session

def init_llm(nsfw_mode: bool = False, api_type: str = "openai", **kwargs):
    """
    Initializes LLM models based on API type and configuration.
    
    Args:
        nsfw_mode: Whether to enable NSFW mode
        api_type: "gemini" or "openai"
        **kwargs: Additional configuration (api_key, base_url, model, etc.)
    """
    global current_api_type, chat_session
    
    current_api_type = api_type
    
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
    global chat_history
    
    if current_api_type == "openai":
        if not is_openai_configured():
            error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
            yield error_msg
            yield ("__FINAL_RESULT__", error_msg, "None")
            return
        
        # For OpenAI, use chat history instead of session
        try:
            stream_gen = get_openai_conversation_response_stream(chat_history, user_message, critique)
            ai_response = ""
            trait = "None"
            
            for chunk in stream_gen:
                if isinstance(chunk, tuple) and len(chunk) == 3 and chunk[0] == "__FINAL_RESULT__":
                    # This is the final result tuple
                    _, ai_response, trait = chunk
                    break
                yield chunk
            
            # Update chat history
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": ai_response})
            yield ("__FINAL_RESULT__", ai_response, trait)
                
        except Exception as e:
            error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
            print(error_message)
            yield error_message
            yield ("__FINAL_RESULT__", error_message, "None")
    
    elif current_api_type == "gemini":
        if not is_gemini_configured():
            error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
            yield error_msg
            yield ("__FINAL_RESULT__", error_msg, "None")
            return

        try:
            stream_gen = get_gemini_conversation_response_stream(chat_session, user_message, critique)
            for chunk in stream_gen:
                yield chunk
                
        except Exception as e:
            error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
            print(error_message)
            yield error_message
            yield ("__FINAL_RESULT__", error_message, "None")

def evaluate_profile(full_profile: str) -> dict:
    """
    Gets a diagnostic report from the evaluator model.
    Supports both Gemini and OpenAI-compatible APIs.
    """
    if current_api_type == "openai":
        return evaluate_openai_profile(full_profile)
    
    elif current_api_type == "gemini":
        return evaluate_gemini_profile(full_profile)
    
    else:
        return {"is_ready_for_writing": False, "critique": lang_manager.t("ERROR_LLM_NOT_CONFIGURED")}

def write_final_prompt_stream(full_profile: str):
    """
    Gets the final, formatted System Prompt from the writer model as a stream.
    Supports both Gemini and OpenAI-compatible APIs.
    """
    if current_api_type == "openai":
        for chunk in write_openai_final_prompt_stream(full_profile):
            yield chunk
        return
    
    elif current_api_type == "gemini":
        for chunk in write_gemini_final_prompt_stream(full_profile):
            yield chunk
        return
    
    else:
        yield lang_manager.t("ERROR_LLM_NOT_CONFIGURED")

def start_chat_session():
    """Starts a new chat session with the conversation model."""
    global chat_history, chat_session
    
    if current_api_type == "openai":
        # Reset chat history for OpenAI
        chat_history = []
        return "openai_session"  # Return a placeholder
    
    elif current_api_type == "gemini":
        # Start Gemini chat session
        chat_session = start_gemini_chat_session()
        return chat_session
    
    else:
        return None

def get_current_api_type() -> str:
    """Get current API type"""
    return current_api_type

def reset_chat_history():
    """Reset chat history for OpenAI sessions"""
    global chat_history
    chat_history = []