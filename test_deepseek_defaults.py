#!/usr/bin/env python3
"""
测试DeepSeek默认配置
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from openai_helper import openai_config, is_openai_configured, get_openai_config
import llm_helper

def test_deepseek_defaults():
    """测试DeepSeek默认配置"""
    print("=== 测试DeepSeek默认配置 ===")
    
    print("1. 检查默认配置...")
    print(f"默认base_url: {openai_config['base_url']}")
    print(f"默认model: {openai_config['model']}")
    print(f"配置状态: {is_openai_configured()}")
    
    print("\n2. 测试配置显示...")
    config_display = get_openai_config()
    print(f"配置显示: {config_display}")
    
    print("\n3. 测试带API密钥的初始化...")
    result = llm_helper.init_llm(
        api_type="openai",
        api_key="sk-test123456789",
        base_url=openai_config['base_url'],  # 使用默认值
        model=openai_config['model']  # 使用默认值
    )
    print(f"初始化结果: {result}")
    print(f"配置状态: {is_openai_configured()}")
    print(f"当前API类型: {llm_helper.get_current_api_type()}")

if __name__ == "__main__":
    test_deepseek_defaults()
