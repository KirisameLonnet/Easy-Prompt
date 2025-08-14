"""
Handles all interactions with LLM APIs, supporting both Google Generative AI
and OpenAI-compatible APIs (OpenAI, Claude, DeepSeek, etc.)
"""
import os
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from language_manager import lang_manager
from openai_helper import (
    init_openai_llm, is_openai_configured,
    get_openai_conversation_response_stream,
    evaluate_openai_profile,
    write_openai_final_prompt_stream
)

# --- Model Configurations ---
CONVERSATION_MODEL = None
EVALUATOR_MODEL = None
WRITER_MODEL = None

# --- API Type Configuration ---
current_api_type = "gemini"  # "gemini" or "openai"
chat_history = []  # For OpenAI-style chat history

def init_llm(nsfw_mode: bool = False, api_type: str = "gemini", **kwargs):
    """
    Initializes LLM models based on API type and configuration.
    
    Args:
        nsfw_mode: Whether to enable NSFW mode (only for Gemini)
        api_type: "gemini" or "openai"
        **kwargs: Additional configuration for OpenAI (api_key, base_url, model, etc.)
    """
    global CONVERSATION_MODEL, EVALUATOR_MODEL, WRITER_MODEL, current_api_type
    
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
    
    else:
        # Initialize Gemini API (original logic)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            print(lang_manager.t("ERROR_LLM_NOT_CONFIGURED"))
            return False

        genai.configure(api_key=api_key)

        safety_settings = None
        if nsfw_mode:
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

        # --- Model Initialization ---
        conv_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        eval_model_name = os.getenv("EVALUATOR_MODEL", "gemini-2.5-flash")
        prompts = lang_manager.system_prompts

        CONVERSATION_MODEL = genai.GenerativeModel(
            conv_model_name,
            system_instruction=prompts.get_conversation_system_prompt(nsfw_mode),
            safety_settings=safety_settings
        )
        EVALUATOR_MODEL = genai.GenerativeModel(
            eval_model_name,
            system_instruction=prompts.get_evaluator_system_prompt(nsfw_mode),
            safety_settings=safety_settings
        )
        
        writer_generation_config = {"temperature": 0.7} # Keep writer deterministic
        WRITER_MODEL = genai.GenerativeModel(
            conv_model_name,
            system_instruction=prompts.get_writer_system_prompt(nsfw_mode),
            safety_settings=safety_settings,
            generation_config=writer_generation_config
        )
        
        print(lang_manager.t("LLMS_INITIALIZED", conv_model=conv_model_name, eval_model=eval_model_name))
        if nsfw_mode:
            print("🔥 " + lang_manager.t("NSFW_MODE_ACTIVE_FULL_WARNING") + " 🔥")
        return True

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
            raise StopIteration((error_msg, "None"))
        
        # For OpenAI, use chat history instead of session
        try:
            stream = get_openai_conversation_response_stream(chat_history, user_message, critique)
            for chunk in stream:
                yield chunk
        except StopIteration as e:
            # Extract the final result from StopIteration
            ai_response, trait = e.value
            # Update chat history
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": ai_response})
            raise StopIteration((ai_response, trait))
    
    else:
        # Original Gemini logic
        if not CONVERSATION_MODEL:
            error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
            yield error_msg
            raise StopIteration((error_msg, "None"))

        try:
            message_with_context = f"诊断报告: {critique}\n\n---\n\n用户: {user_message}"
            stream = chat_session.send_message(message_with_context, stream=True)
            full_response_text = ""
            ai_response_part = ""
            trait_part = ""
            found_separator = False
            
            for chunk in stream:
                if chunk.parts:
                    chunk_text = chunk.text
                    full_response_text += chunk_text
                    
                    # 检查是否遇到分隔符
                    if not found_separator:
                        if '---' in chunk_text:
                            # 找到分隔符，分割当前块
                            parts = chunk_text.split('---', 1)
                            ai_response_part += parts[0]
                            # 只 yield 分隔符之前的内容
                            if parts[0]:
                                yield parts[0]
                            
                            found_separator = True
                            # 分隔符之后的内容是 trait 部分
                            if len(parts) > 1:
                                trait_part += parts[1]
                        else:
                            # 还没遇到分隔符，正常输出
                            ai_response_part += chunk_text
                            yield chunk_text
                    else:
                        # 已经遇到分隔符，后续内容都是 trait 部分，不再 yield
                        trait_part += chunk_text
            
            # 清理 trait 部分
            trait_part = trait_part.strip()
            if not trait_part or trait_part.lower() == "none":
                trait_part = "None"
                
            raise StopIteration((ai_response_part.strip(), trait_part))

        except StopIteration:
            # 重新抛出StopIteration
            raise
        except Exception as e:
            error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
            print(error_message)
            yield error_message
            raise StopIteration((error_message, "None"))

def evaluate_profile(full_profile: str) -> dict:
    """
    Gets a diagnostic report from the evaluator model.
    Supports both Gemini and OpenAI-compatible APIs.
    """
    if current_api_type == "openai":
        return evaluate_openai_profile(full_profile)
    
    else:
        # Original Gemini logic
        if not EVALUATOR_MODEL:
            return {"is_ready_for_writing": False, "critique": lang_manager.t("ERROR_LLM_NOT_CONFIGURED")}
        
        try:
            response = EVALUATOR_MODEL.generate_content(full_profile)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        except Exception as e:
            error_message = lang_manager.t("ERROR_EVALUATOR_LLM", error=e)
            print(error_message)
            return {"is_ready_for_writing": False, "critique": error_message}

def write_final_prompt_stream(full_profile: str):
    """
    Gets the final, formatted System Prompt from the writer model as a stream.
    Supports both Gemini and OpenAI-compatible APIs.
    """
    if current_api_type == "openai":
        for chunk in write_openai_final_prompt_stream(full_profile):
            yield chunk
        return
    
    else:
        # Original Gemini logic
        if not WRITER_MODEL:
            yield lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
            return
            
        try:
            response_stream = WRITER_MODEL.generate_content(full_profile, stream=True)
            for chunk in response_stream:
                if chunk.parts:
                    yield chunk.text
        except Exception as e:
            error_message = lang_manager.t("ERROR_WRITER_LLM", error=e)
            print(error_message)
            yield error_message

def start_chat_session():
    """Starts a new chat session with the conversation model."""
    global chat_history
    
    if current_api_type == "openai":
        # Reset chat history for OpenAI
        chat_history = []
        return "openai_session"  # Return a placeholder
    
    else:
        # Original Gemini logic
        if not CONVERSATION_MODEL:
            return None
        return CONVERSATION_MODEL.start_chat(history=[])

def get_current_api_type() -> str:
    """Get current API type"""
    return current_api_type

def reset_chat_history():
    """Reset chat history for OpenAI sessions"""
    global chat_history
    chat_history = []