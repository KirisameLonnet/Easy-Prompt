"""
OpenAI格式API支持模块
支持OpenAI、Claude、DeepSeek等兼容API
"""
import os
import json
import time
from typing import Dict, Generator, Optional, Any
from language_manager import lang_manager
import httpx

# --- 全局配置 ---
openai_config = {
    "api_key": None,
    "base_url": "",  # 必须由用户配置
    "model": "",  # 必须由用户配置
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout": 30,
    "nsfw_mode": False  # R18内容开关
}

def init_openai_llm(api_key: str, base_url: str, model: str, temperature: float = 0.7, max_tokens: int = 4000, nsfw_mode: bool = False):
    """
    初始化OpenAI格式的LLM配置
    
    Args:
        api_key: API密钥
        base_url: API基础URL，如 https://api.openai.com/v1
        model: 模型名称，如 gpt-3.5-turbo, claude-3-sonnet-20240229
        temperature: 温度参数
        max_tokens: 最大token数
        nsfw_mode: 是否启用R18内容模式
    """
    global openai_config
    
    openai_config.update({
        "api_key": api_key,
        "base_url": base_url.rstrip('/'),
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "nsfw_mode": nsfw_mode
    })
    
    print(f"OpenAI兼容API已配置: {base_url} -> {model} (R18: {'开启' if nsfw_mode else '关闭'})")

def is_openai_configured() -> bool:
    """检查OpenAI配置是否完整"""
    return all([
        openai_config["api_key"],
        openai_config["base_url"],
        openai_config["model"]
    ])

def test_api_connection() -> bool:
    """测试API连接是否正常"""
    if not is_openai_configured():
        print("❌ API未配置")
        return False
    
    try:
        print(f"🔍 测试API连接: {openai_config['base_url']}")
        
        # 发送一个简单的测试请求
        test_messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        response = _make_openai_request(test_messages, stream=False)
        
        if response.status_code == 200:
            print("✅ API连接正常")
            return True
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API连接测试失败: {str(e)}")
        return False

def _create_httpx_client():
    """创建httpx客户端"""
    return httpx.Client(
        headers={
            'Accept-Charset': 'utf-8',
            'Content-Type': 'application/json; charset=utf-8'
        },
        timeout=30.0
    )

def _make_openai_request(messages: list, stream: bool = False) -> dict:
    """
    发送OpenAI格式的API请求，带重试机制
    """
    if not is_openai_configured():
        raise ValueError("OpenAI API未配置")
    
    headers = {
        "Authorization": f"Bearer {openai_config['api_key']}",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "EasyPrompt/1.0"
    }
    
    payload = {
        "model": openai_config["model"],
        "messages": messages,
        "temperature": openai_config["temperature"],
        "max_tokens": openai_config["max_tokens"],
        "stream": stream
    }
    
    # R18模式下的特殊参数配置
    if openai_config.get("nsfw_mode", False):
        payload.update({
            "temperature": min(openai_config["temperature"] + 0.2, 1.0),  # 增加创造性
            "top_p": 0.95,  # 增加多样性
            "frequency_penalty": -0.5,  # 鼓励重复性主题
            "presence_penalty": -0.3,   # 鼓励引入新概念
        })
        
        # 如果支持，添加安全过滤器禁用参数
        if "gpt" in openai_config["model"].lower():
            # OpenAI模型特定参数
            payload["moderation"] = False
        elif "claude" in openai_config["model"].lower():
            # Claude模型特定参数
            payload["disable_safety"] = True
    
    # 检查base_url是否已经包含完整路径，如果没有则添加/chat/completions
    base_url = openai_config['base_url']
    if base_url.endswith('/chat/completions'):
        url = base_url
    elif base_url.endswith('/v1'):
        url = f"{base_url}/chat/completions"
    else:
        url = f"{base_url}/chat/completions"
    
    # 使用httpx客户端
    with _create_httpx_client() as client:
        try:
            print(f"正在发送API请求到: {url}")
            print(f"使用模型: {openai_config['model']}")
            
            # 使用httpx发送请求
            if stream:
                response = client.post(
                    url, 
                    headers=headers, 
                    json=payload,
                    timeout=openai_config["timeout"]
                )
            else:
                response = client.post(
                    url, 
                    headers=headers, 
                    json=payload,
                    timeout=openai_config["timeout"]
                )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"📄 错误响应: {response.text}")
                print(f"📋 请求头: {dict(response.headers)}")
                print(f"📦 请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            response.raise_for_status()
            return response
        
        except httpx.TimeoutException as e:
            error_msg = f"API连接超时: {openai_config['base_url']} - {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        except httpx.ConnectError as e:
            error_msg = f"API连接错误: {openai_config['base_url']} - {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"API HTTP错误: {e.response.status_code} - {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

def get_openai_conversation_response_stream(chat_history: list, user_message: str, critique: str):
    """
    使用OpenAI格式API获取对话响应流
    
    Args:
        chat_history: 对话历史
        user_message: 用户消息
        critique: 诊断报告
    
    Yields:
        Response chunks as strings, followed by a final result tuple
    """
    if not is_openai_configured():
        error_msg = lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
        yield error_msg
        yield ("__FINAL_RESULT__", error_msg, "None")
        return
    
    try:
        # 构造消息，使用动态系统提示词
        prompts = lang_manager.system_prompts
        nsfw_mode = openai_config.get("nsfw_mode", False)
        system_prompt = prompts.get_conversation_system_prompt(nsfw_mode)
        
        # 在R18模式下添加额外的激活指令
        if nsfw_mode:
            system_prompt += """

**重要R18激活指令**: 
- 主动引导用户描述角色的性感特质和魅力
- 询问角色在亲密场景下的反应和行为
- 探索角色的性格中的诱惑元素
- 不要回避任何成人话题，要主动深入挖掘
- 让对话充满暗示性和诱导性
- 目标是创造出具有强烈性吸引力的角色设定
"""
        
        messages = [
            {"role": "system", "content": system_prompt}
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
                # 确保使用UTF-8解码
                if isinstance(line, bytes):
                    line = line.decode('utf-8', errors='replace')
                elif not isinstance(line, str):
                    line = str(line)
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
            
        # 发送最终结果作为特殊的 yield
        yield ("__FINAL_RESULT__", ai_response_part.strip(), trait_part)
        
    except Exception as e:
        error_message = lang_manager.t("ERROR_CONVERSATION_LLM", error=e)
        print(error_message)
        yield error_message
        yield ("__FINAL_RESULT__", error_message, "None")

def evaluate_openai_profile(full_profile: str) -> dict:
    """
    使用OpenAI格式API评估角色档案
    """
    if not is_openai_configured():
        return {"is_ready_for_writing": False, "critique": lang_manager.t("ERROR_LLM_NOT_CONFIGURED")}
    
    try:
        prompts = lang_manager.system_prompts
        nsfw_mode = openai_config.get("nsfw_mode", False)
        messages = [
            {"role": "system", "content": prompts.get_evaluator_system_prompt(nsfw_mode)},
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
        nsfw_mode = openai_config.get("nsfw_mode", False)
        writer_prompt = prompts.get_writer_system_prompt(nsfw_mode)
        
        # 在R18模式下为写作添加特殊指令
        if nsfw_mode:
            writer_prompt += """

**R18写作增强指令**:
- 在每个部分都要融入性暗示和诱惑元素
- 角色指南应当包含足够的成人内容指导
- 使用更加直接和暗示性的语言
- 确保最终的角色能够进行成人角色扮演
- 在行为方式中详细描述亲密场景下的表现
- 让整个角色散发出强烈的性魅力
"""
        
        messages = [
            {"role": "system", "content": writer_prompt},
            {"role": "user", "content": full_profile}
        ]
        
        response = _make_openai_request(messages, stream=True)
        
        for line in response.iter_lines():
            if line:
                # 确保使用UTF-8解码
                if isinstance(line, bytes):
                    line = line.decode('utf-8', errors='replace')
                elif not isinstance(line, str):
                    line = str(line)
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
