#!/usr/bin/env python3
"""
R18模式场景想象功能测试脚本
验证增强的场景创作和想象力功能
"""

import os
import sys
from language_manager import lang_manager

def test_enhanced_r18_prompts():
    """测试增强的R18模式功能"""
    
    print("=== 增强R18模式功能测试 ===\n")
    
    # 测试对话系统的场景想象功能
    print("1. 对话系统 - 场景想象功能:")
    print("-" * 60)
    conversation_prompt = lang_manager.system_prompts.get_conversation_system_prompt(nsfw_mode=True)
    
    # 查找场景想象部分
    if "场景想象与创作指导" in conversation_prompt:
        print("✅ 场景想象功能已添加到对话系统")
        lines = conversation_prompt.split('\n')
        in_scene_section = False
        for line in lines:
            if "场景想象与创作指导" in line:
                in_scene_section = True
            elif in_scene_section and line.startswith('**') and "场景想象" not in line:
                break
            if in_scene_section:
                print(f"  {line}")
    else:
        print("❌ 场景想象功能未找到")
    
    print("\n" + "="*60)
    
    # 测试写作系统的场景创作功能
    print("2. 写作系统 - 场景创作功能:")
    print("-" * 60)
    writer_prompt = lang_manager.system_prompts.get_writer_system_prompt(nsfw_mode=True)
    
    # 查找场景创作部分
    if "场景创作与想象力" in writer_prompt:
        print("✅ 场景创作功能已添加到写作系统")
        lines = writer_prompt.split('\n')
        in_creation_section = False
        for line in lines:
            if "场景创作与想象力" in line:
                in_creation_section = True
            elif in_creation_section and line.startswith('**') and "场景创作" not in line:
                break
            if in_creation_section:
                print(f"  {line}")
    else:
        print("❌ 场景创作功能未找到")
    
    print("\n" + "="*60)
    
    # 检查提示词写作要求
    if "提示词写作要求" in writer_prompt:
        print("3. 提示词写作要求:")
        print("-" * 60)
        print("✅ 提示词写作要求已添加")
        lines = writer_prompt.split('\n')
        in_writing_section = False
        for line in lines:
            if "提示词写作要求" in line:
                in_writing_section = True
            elif in_writing_section and line.startswith('最终输出'):
                break
            if in_writing_section:
                print(f"  {line}")
    
    print("\n=== 测试完成 ===")

def test_r18_mode_activation():
    """测试R18模式激活状态"""
    
    print("\n=== R18模式激活测试 ===\n")
    
    # 测试普通模式
    normal_prompt = lang_manager.system_prompts.get_conversation_system_prompt(nsfw_mode=False)
    if "R18专业模式" not in normal_prompt:
        print("✅ 普通模式: R18功能正确禁用")
    else:
        print("❌ 普通模式: R18功能意外激活")
    
    # 测试R18模式
    r18_prompt = lang_manager.system_prompts.get_conversation_system_prompt(nsfw_mode=True)
    if "R18专业模式" in r18_prompt:
        print("✅ R18模式: 成人功能正确激活")
    else:
        print("❌ R18模式: 成人功能未激活")
    
    # 检查关键功能
    features = [
        "场景想象与创作指导",
        "提示词创作原则",
        "主动构思和描述各种成人情境场景",
        "详细想象角色在亲密时刻的具体表现"
    ]
    
    print("\n检查关键功能:")
    for feature in features:
        if feature in r18_prompt:
            print(f"✅ {feature}")
        else:
            print(f"❌ {feature}")

if __name__ == "__main__":
    test_enhanced_r18_prompts()
    test_r18_mode_activation()
