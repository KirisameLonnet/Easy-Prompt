#!/usr/bin/env python3
"""
API连接诊断工具
"""

import os
import sys
from openai_helper import init_openai_llm, test_api_connection, is_openai_configured

def diagnose_api():
    """诊断API连接问题"""
    print("=== API连接诊断工具 ===\n")
    
    # 检查环境变量
    print("1. 检查环境变量:")
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('MOONSHOT_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL') or os.getenv('MOONSHOT_BASE_URL')
    model = os.getenv('OPENAI_MODEL') or os.getenv('MOONSHOT_MODEL')
    
    print(f"   API Key: {'已设置' if api_key else '❌ 未设置'}")
    print(f"   Base URL: {base_url or '❌ 未设置'}")
    print(f"   Model: {model or '❌ 未设置'}")
    
    if not api_key:
        print("\n❌ 请设置API密钥环境变量:")
        print("   export OPENAI_API_KEY='your-api-key'")
        print("   或")
        print("   export MOONSHOT_API_KEY='your-api-key'")
        return False
    
    # 设置默认值
    if not base_url:
        base_url = "https://api.moonshot.cn/v1"
        print(f"   使用默认Base URL: {base_url}")
    
    if not model:
        model = "kimi-k2-turbo-preview"
        print(f"   使用默认Model: {model}")
    
    print("\n2. 初始化API配置:")
    try:
        init_openai_llm(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.7,
            max_tokens=4000
        )
        print("   ✅ API配置成功")
    except Exception as e:
        print(f"   ❌ API配置失败: {e}")
        return False
    
    print("\n3. 测试API连接:")
    if test_api_connection():
        print("   ✅ API连接正常")
        return True
    else:
        print("   ❌ API连接失败")
        
        print("\n4. 故障排除建议:")
        print("   - 检查网络连接")
        print("   - 验证API密钥是否正确")
        print("   - 确认API服务是否可用")
        print("   - 检查防火墙设置")
        print("   - 尝试使用VPN（如果在中国大陆）")
        
        return False

def suggest_alternatives():
    """建议替代方案"""
    print("\n=== 替代方案建议 ===")
    print("1. 使用DeepSeek API (免费额度):")
    print("   export OPENAI_API_KEY='your-deepseek-key'")
    print("   export OPENAI_BASE_URL='https://api.deepseek.com/v1'")
    print("   export OPENAI_MODEL='deepseek-chat'")
    
    print("\n2. 使用OpenAI API:")
    print("   export OPENAI_API_KEY='your-openai-key'")
    print("   export OPENAI_BASE_URL='https://api.openai.com/v1'")
    print("   export OPENAI_MODEL='gpt-3.5-turbo'")
    
    print("\n3. 使用本地模型 (需要额外配置):")
    print("   - Ollama")
    print("   - LM Studio")
    print("   - 其他本地LLM服务")

if __name__ == "__main__":
    success = diagnose_api()
    
    if not success:
        suggest_alternatives()
        sys.exit(1)
    else:
        print("\n🎉 API连接正常，可以正常使用！")
        sys.exit(0)
