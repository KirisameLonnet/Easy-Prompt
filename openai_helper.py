"""
OpenAI格式API支持模块
支持OpenAI、Claude、DeepSeek等兼容API
"""
import os
import json
import requests
from typing import Dict, Generator, Optional, Any
from language_manager import lang_manager

# --- 全局配置 ---
openai_config = {
    "api_key": None,
    "base_url": "https://api.deepseek.com/v1",  # 默认使用DeepSeek
    "model": "deepseek-chat",  # 默认使用DeepSeek Chat模型
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout": 30
}

def init_openai_llm(api_key: str, base_url: str, model: str, temperature: float = 0.7, max_tokens: int = 4000):
    """
    初始化OpenAI格式的LLM配置
    
    Args:
        api_key: API密钥
        base_url: API基础URL，如 https://api.openai.com/v1
        model: 模型名称，如 gpt-3.5-turbo, claude-3-sonnet-20240229
        temperature: 温度参数
        max_tokens: 最大token数
    """
    global openai_config
    
    openai_config.update({
        "api_key": api_key,
        "base_url": base_url.rstrip('/'),
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens
    })
    
    print(f"OpenAI兼容API已配置: {base_url} -> {model}")

def is_openai_configured() -> bool:
    """检查OpenAI配置是否完整"""
    return all([
        openai_config["api_key"],
        openai_config["base_url"],
        openai_config["model"]
    ])

def _make_openai_request(messages: list, stream: bool = False) -> dict:
    """
    发送OpenAI格式的API请求
    """
    if not is_openai_configured():
        raise ValueError("OpenAI API未配置")
    
    headers = {
        "Authorization": f"Bearer {openai_config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": openai_config["model"],
        "messages": messages,
        "temperature": openai_config["temperature"],
        "max_tokens": openai_config["max_tokens"],
        "stream": stream
    }
    
    url = f"{openai_config['base_url']}/chat/completions"
    
    try:
        if stream:
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                stream=True, 
                timeout=openai_config["timeout"]
            )
        else:
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=openai_config["timeout"]
            )
        
        response.raise_for_status()
        return response
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenAI API请求失败: {str(e)}")

def get_openai_conversation_response_stream(chat_history: list, user_message: str, critique: str):
    """
    使用OpenAI格式API获取对话响应流
    
    Args:
        chat_history: 对话历史
        user_message: 用户消息
        critique: 诊断报告
    
    Yields:
        Response chunks as strings
    
    Returns:
        Final (ai_response, trait) tuple via StopIteration exception value
    """
    if not is_openai_configured():
        error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
        yield error_msg
        raise StopIteration((error_msg, "None"))
    
    try:
        # 构造消息
        prompts = lang_manager.system_prompts
        messages = [
            {"role": "system", "content": prompts.CONVERSATION_SYSTEM_PROMPT}
        ]
        
        # 添加历史对话
        messages.extend(chat_history)
        
        # 添加当前消息
        message_with_context = f"诊断报告: {critique}\n\n---\n\n用户: {user_message}"
        messages.append({"role": "user", "content": message_with_context})
        
        response = _make_openai_request(messages, stream=True)
        
        full_response_text = ""
        ai_response_part = ""
        trait_part = ""
        found_separator = False
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk_data = json.loads(data)
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            delta = chunk_data['choices'][0].get('delta', {})
                            chunk_text = delta.get('content', '')
                            
                            if chunk_text:
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
                    except json.JSONDecodeError:
                        continue
        
        # 清理 trait 部分
        trait_part = trait_part.strip()
        if not trait_part or trait_part.lower() == "none":
            trait_part = "None"
            
        # 通过StopIteration返回最终结果
        raise StopIteration((ai_response_part.strip(), trait_part))
        
    except StopIteration:
        # 重新抛出StopIteration
        raise
    except Exception as e:
        error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
        print(error_message)
        yield error_message
        raise StopIteration((error_message, "None"))

def evaluate_openai_profile(full_profile: str) -> dict:
    """
    使用OpenAI格式API评估角色档案
    """
    if not is_openai_configured():
        return {"is_ready_for_writing": False, "critique": lang_manager.t("ERROR_LLM_NOT_CONFIGURED")}
    
    try:
        prompts = lang_manager.system_prompts
        messages = [
            {"role": "system", "content": prompts.EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": full_profile}
        ]
        
        response = _make_openai_request(messages, stream=False)
        response_data = response.json()
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            content = response_data['choices'][0]['message']['content']
            cleaned_response = content.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        else:
            raise Exception("API响应格式错误")
            
    except Exception as e:
        error_message = lang_manager.t("ERROR_EVALUATOR_LLM", error=e)
        print(error_message)
        return {"is_ready_for_writing": False, "critique": error_message}

def write_openai_final_prompt_stream(full_profile: str) -> Generator[str, None, None]:
    """
    使用OpenAI格式API生成最终提示词流
    """
    if not is_openai_configured():
        yield lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
        return
        
    try:
        prompts = lang_manager.system_prompts
        messages = [
            {"role": "system", "content": prompts.WRITER_SYSTEM_PROMPT},
            {"role": "user", "content": full_profile}
        ]
        
        response = _make_openai_request(messages, stream=True)
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk_data = json.loads(data)
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            delta = chunk_data['choices'][0].get('delta', {})
                            chunk_text = delta.get('content', '')
                            
                            if chunk_text:
                                yield chunk_text
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        error_message = lang_manager.t("ERROR_WRITER_LLM", error=e)
        print(error_message)
        yield error_message

def get_openai_config() -> dict:
    """获取当前OpenAI配置（隐藏敏感信息）"""
    config = openai_config.copy()
    if config["api_key"]:
        # 只显示API密钥的前4位和后4位
        key = config["api_key"]
        if len(key) > 8:
            config["api_key"] = f"{key[:4]}...{key[-4:]}"
    return config
