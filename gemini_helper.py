"""
Google Gemini API 支持模块
支持前端配置 API Key 和模型选择
"""
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import Dict, Generator, Optional
from language_manager import lang_manager

# --- 全局配置 ---
gemini_config = {
    "api_key": None,
    "model": "gemini-2.5-flash",  # 默认对话模型
    "evaluator_model": "gemini-2.5-flash",  # 默认评估模型
    "temperature": 0.7,
    "nsfw_mode": False  # R18内容开关
}

# --- Model Instances ---
CONVERSATION_MODEL = None
EVALUATOR_MODEL = None
WRITER_MODEL = None

def init_gemini_llm(api_key: str, model: str = "gemini-2.5-flash", evaluator_model: str = None, temperature: float = 0.7, nsfw_mode: bool = False):
    """
    初始化Gemini API配置
    
    Args:
        api_key: Google API密钥
        model: 对话模型名称
        evaluator_model: 评估模型名称，默认与对话模型相同
        temperature: 温度参数
        nsfw_mode: 是否启用R18内容模式
    """
    global gemini_config, CONVERSATION_MODEL, EVALUATOR_MODEL, WRITER_MODEL
    
    if not evaluator_model:
        evaluator_model = model
    
    gemini_config.update({
        "api_key": api_key,
        "model": model,
        "evaluator_model": evaluator_model,
        "temperature": temperature,
        "nsfw_mode": nsfw_mode
    })
    
    try:
        # 配置Gemini API
        genai.configure(api_key=api_key)
        
        # 安全设置
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
        
        # 初始化模型
        CONVERSATION_MODEL = genai.GenerativeModel(
            model,
            system_instruction=prompts.get_conversation_system_prompt(nsfw_mode),
            safety_settings=safety_settings
        )
        
        EVALUATOR_MODEL = genai.GenerativeModel(
            evaluator_model,
            system_instruction=prompts.get_evaluator_system_prompt(nsfw_mode),
            safety_settings=safety_settings
        )
        
        writer_generation_config = {"temperature": temperature}
        WRITER_MODEL = genai.GenerativeModel(
            model,
            system_instruction=prompts.get_writer_system_prompt(nsfw_mode),
            safety_settings=safety_settings,
            generation_config=writer_generation_config
        )
        
        print(f"Gemini API已配置: {model} (评估: {evaluator_model}) (R18: {'开启' if nsfw_mode else '关闭'})")
        return True
        
    except Exception as e:
        print(f"Gemini API初始化失败: {e}")
        return False

def is_gemini_configured() -> bool:
    """检查Gemini配置是否完整"""
    return all([
        gemini_config["api_key"],
        gemini_config["model"],
        CONVERSATION_MODEL is not None
    ])

def get_gemini_conversation_response_stream(chat_session, user_message: str, critique: str):
    """
    使用Gemini API获取对话响应流
    
    Args:
        chat_session: Gemini聊天会话
        user_message: 用户消息
        critique: 诊断报告
    
    Yields:
        Response chunks as strings, followed by a final result tuple
    """
    if not is_gemini_configured():
        error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
        yield error_msg
        yield ("__FINAL_RESULT__", error_msg, "None")
        return

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
            
        yield ("__FINAL_RESULT__", ai_response_part.strip(), trait_part)

    except Exception as e:
        error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
        print(error_message)
        yield error_message
        yield ("__FINAL_RESULT__", error_message, "None")

def evaluate_gemini_profile(full_profile: str) -> dict:
    """
    使用Gemini API评估角色档案
    """
    if not is_gemini_configured():
        return {"is_ready_for_writing": False, "critique": lang_manager.t("ERROR_LLM_NOT_CONFIGURED")}
    
    try:
        response = EVALUATOR_MODEL.generate_content(full_profile)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
    except Exception as e:
        error_message = lang_manager.t("ERROR_EVALUATOR_LLM", error=e)
        print(error_message)
        return {"is_ready_for_writing": False, "critique": error_message}

def write_gemini_final_prompt_stream(full_profile: str) -> Generator[str, None, None]:
    """
    使用Gemini API生成最终提示词流
    """
    if not is_gemini_configured():
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

def start_gemini_chat_session():
    """启动新的Gemini聊天会话"""
    if not is_gemini_configured():
        return None
    return CONVERSATION_MODEL.start_chat(history=[])

def get_gemini_config() -> dict:
    """获取当前Gemini配置（隐藏敏感信息）"""
    config = gemini_config.copy()
    if config["api_key"]:
        # 只显示API密钥的前4位和后4位
        key = config["api_key"]
        if len(key) > 8:
            config["api_key"] = f"{key[:4]}...{key[-4:]}"
    return config
