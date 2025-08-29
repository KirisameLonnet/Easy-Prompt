#!/usr/bin/env python3
"""
R18模式测试脚本
验证增强的成人内容生成功能
"""

import os
import sys
from language_manager import lang_manager

def test_r18_prompts():
    """测试R18模式下的系统提示词"""
    
    print("=== R18模式系统提示词测试 ===\n")
    
    # 测试对话系统提示词
    print("1. 对话系统提示词 (R18模式):")
    print("-" * 50)
    conversation_prompt = lang_manager.system_prompts.get_conversation_system_prompt(nsfw_mode=True)
    print(conversation_prompt[:500] + "...\n")
    
    # 测试评估系统提示词
    print("2. 评估系统提示词 (R18模式):")
    print("-" * 50)
    evaluator_prompt = lang_manager.system_prompts.get_evaluator_system_prompt(nsfw_mode=True)
    print(evaluator_prompt[:500] + "...\n")
    
    # 测试写作系统提示词
    print("3. 写作系统提示词 (R18模式):")
    print("-" * 50)
    writer_prompt = lang_manager.system_prompts.get_writer_system_prompt(nsfw_mode=True)
    print(writer_prompt[:500] + "...\n")
    
    print("=== 测试完成 ===")

def test_openai_r18_config():
    """测试OpenAI API的R18配置"""
    
    print("=== OpenAI R18配置测试 ===\n")
    
    try:
        from openai_helper import openai_config, init_openai_llm
        
        # 初始化R18模式
        init_openai_llm(
            api_key="test_key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            nsfw_mode=True
        )
        
        print("OpenAI R18配置:")
        print(f"  NSFW模式: {openai_config.get('nsfw_mode', False)}")
        print(f"  模型: {openai_config.get('model')}")
        print(f"  温度: {openai_config.get('temperature')}")
        
        print("\n✅ OpenAI R18配置测试通过")
        
    except Exception as e:
        print(f"❌ OpenAI R18配置测试失败: {e}")

if __name__ == "__main__":
    test_r18_prompts()
    print()
    test_openai_r18_config()
