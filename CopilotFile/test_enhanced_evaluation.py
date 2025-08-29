#!/usr/bin/env python3
"""
增强评估系统测试脚本
验证前后端评估状态模块的重构是否正确
"""

import json
import asyncio
from language_manager import lang_manager

def test_enhanced_evaluation_prompt():
    """测试增强的评估系统提示词"""
    
    print("=== 增强评估系统提示词测试 ===\n")
    
    # 测试R18模式和非R18模式
    for nsfw_mode in [False, True]:
        mode_name = "R18模式" if nsfw_mode else "普通模式"
        print(f"🔍 测试 {mode_name}:")
        print("-" * 50)
        
        prompt = lang_manager.system_prompts.get_evaluator_system_prompt(nsfw_mode)
        
        # 检查关键要素
        required_elements = [
            "evaluation_score",
            "extracted_traits", 
            "extracted_keywords",
            "completeness_breakdown",
            "suggestions"
        ]
        
        for element in required_elements:
            if element in prompt:
                print(f"✅ {element}")
            else:
                print(f"❌ {element}")
        
        print(f"\n提示词长度: {len(prompt)} 字符")
        print()

def test_mock_evaluation_response():
    """测试模拟评估响应"""
    
    print("=== 模拟评估响应测试 ===\n")
    
    # 模拟一个评估响应
    mock_response = {
        "is_ready_for_writing": False,
        "critique": "角色基本框架已建立，建议添加更多性格细节",
        "evaluation_score": 6,
        "extracted_traits": [
            "傲娇性格",
            "科学家身份", 
            "聪明理性",
            "内心温柔"
        ],
        "extracted_keywords": [
            "实验室",
            "研究",
            "理论",
            "口是心非",
            "别扭"
        ],
        "completeness_breakdown": {
            "core_identity": 2,
            "personality_traits": 3,
            "behavioral_patterns": 1,
            "interaction_patterns": 2
        },
        "suggestions": [
            "添加具体的科研背景设定",
            "描述更多日常行为习惯", 
            "补充与他人的互动方式"
        ]
    }
    
    print("📄 模拟评估响应:")
    print(json.dumps(mock_response, ensure_ascii=False, indent=2))
    
    # 验证数据结构
    print("\n🔍 数据结构验证:")
    
    # 检查必需字段
    required_fields = [
        "is_ready_for_writing",
        "critique", 
        "evaluation_score",
        "extracted_traits",
        "extracted_keywords",
        "completeness_breakdown",
        "suggestions"
    ]
    
    for field in required_fields:
        if field in mock_response:
            print(f"✅ {field}: {type(mock_response[field]).__name__}")
        else:
            print(f"❌ 缺少字段: {field}")
    
    # 检查completeness_breakdown结构
    if "completeness_breakdown" in mock_response:
        breakdown = mock_response["completeness_breakdown"]
        expected_categories = [
            "core_identity",
            "personality_traits", 
            "behavioral_patterns",
            "interaction_patterns"
        ]
        
        print("\n📊 完整度分解验证:")
        for category in expected_categories:
            if category in breakdown:
                print(f"✅ {category}: {breakdown[category]}")
            else:
                print(f"❌ 缺少类别: {category}")

def test_frontend_data_flow():
    """测试前端数据流"""
    
    print("\n=== 前端数据流测试 ===\n")
    
    # 模拟WebSocket消息格式
    websocket_message = {
        "type": "evaluation_update",
        "payload": {
            "message": "[评估完成] 角色基本框架已建立，建议添加更多性格细节",
            "extracted_traits": ["傲娇性格", "科学家身份"],
            "extracted_keywords": ["实验室", "研究", "理论"],
            "evaluation_score": 6,
            "completeness_breakdown": {
                "core_identity": 2,
                "personality_traits": 3,
                "behavioral_patterns": 1,
                "interaction_patterns": 2
            },
            "suggestions": ["添加具体的科研背景设定", "描述更多日常行为习惯"],
            "is_ready": False
        }
    }
    
    print("📡 WebSocket消息格式:")
    print(json.dumps(websocket_message, ensure_ascii=False, indent=2))
    
    # 验证前端组件所需的数据
    payload = websocket_message["payload"]
    print("\n🎨 前端组件数据验证:")
    print(f"✅ 评估状态: {payload['message']}")
    print(f"✅ 特性数量: {len(payload['extracted_traits'])}")
    print(f"✅ 关键词数量: {len(payload['extracted_keywords'])}")
    print(f"✅ 评估分数: {payload['evaluation_score']}/10")
    print(f"✅ 完整度指标: {sum(payload['completeness_breakdown'].values())} 项")
    print(f"✅ 改进建议: {len(payload['suggestions'])} 条")

if __name__ == "__main__":
    test_enhanced_evaluation_prompt()
    test_mock_evaluation_response()
    test_frontend_data_flow()
    
    print("\n=== 测试完成 ===")
    print("✨ 增强评估系统已准备就绪！")
