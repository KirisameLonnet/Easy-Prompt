#!/usr/bin/env python3
"""
简单测试OpenAI兼容API支持
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from openai_helper import init_openai_llm, is_openai_configured, get_openai_config
import llm_helper

def test_openai_init():
    """测试OpenAI配置初始化"""
    print("=== 测试OpenAI API配置 ===")
    
    # 测试无效配置
    print("1. 测试无效配置...")
    result = llm_helper.init_llm(
        api_type="openai",
        api_key="test-key",
        base_url="https://invalid-url.com/v1",
        model="gpt-3.5-turbo"
    )
    print(f"无效配置结果: {result}")
    print(f"配置状态: {is_openai_configured()}")
    print(f"配置信息: {get_openai_config()}")
    
    print("\n2. 测试Gemini配置...")
    result = llm_helper.init_llm(api_type="gemini")
    print(f"Gemini配置结果: {result}")
    print(f"当前API类型: {llm_helper.get_current_api_type()}")

if __name__ == "__main__":
    test_openai_init()
