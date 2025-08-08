"""
Handles all interactions with the Google Generative AI API,
incorporating advanced safety settings and creative configurations.
"""
import os
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from language_manager import lang_manager

# --- Model Configurations ---
CONVERSATION_MODEL = None
EVALUATOR_MODEL = None
WRITER_MODEL = None

def init_llm(nsfw_mode: bool = False):
    """
    Initializes all LLM models based on environment variables and safety settings.
    """
    global CONVERSATION_MODEL, EVALUATOR_MODEL, WRITER_MODEL
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print(lang_manager.t("ERROR_LLM_NOT_CONFIGURED"))
        return

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
        system_instruction=prompts.CONVERSATION_SYSTEM_PROMPT,
        safety_settings=safety_settings
    )
    EVALUATOR_MODEL = genai.GenerativeModel(
        eval_model_name,
        system_instruction=prompts.EVALUATOR_SYSTEM_PROMPT,
        safety_settings=safety_settings
    )
    
    writer_generation_config = {"temperature": 0.7} # Keep writer deterministic
    WRITER_MODEL = genai.GenerativeModel(
        conv_model_name,
        system_instruction=prompts.WRITER_SYSTEM_PROMPT,
        safety_settings=safety_settings,
        generation_config=writer_generation_config
    )
    
    print(lang_manager.t("LLMS_INITIALIZED", conv_model=conv_model_name, eval_model=eval_model_name))
    if nsfw_mode:
        print("🔥 " + lang_manager.t("NSFW_MODE_ACTIVE_FULL_WARNING") + " 🔥")

def get_conversation_response_stream(chat_session, user_message: str, critique: str):
    """
    Gets a streaming response from the conversation model, guided by a critique.
    """
    if not CONVERSATION_MODEL:
        error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
        yield error_msg
        return error_msg, "None"

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
            
        return ai_response_part.strip(), trait_part

    except Exception as e:
        error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
        print(error_message)
        yield error_message
        return error_message, "None"

def evaluate_profile(full_profile: str) -> dict:
    """
    Gets a diagnostic report from the evaluator model.
    """
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
    """
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
    if not CONVERSATION_MODEL:
        return None
    return CONVERSATION_MODEL.start_chat(history=[])