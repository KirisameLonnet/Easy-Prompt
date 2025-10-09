#!/usr/bin/env python3
"""
重构验证测试脚本
测试新的会话管理系统架构是否正常工作
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from session_manager import SessionManager
from storage import FileSystemSessionStore, default_store
from schemas import SessionStatus, ChatMessage, MessageType, EvaluationData


async def test_session_manager():
    """测试 SessionManager 基本功能"""
    print("=" * 60)
    print("测试 SessionManager 基本功能")
    print("=" * 60)
    
    # 使用默认存储创建 SessionManager
    manager = SessionManager(store=default_store)
    
    # 1. 测试创建匿名会话
    print("\n1. 测试创建匿名会话...")
    session1 = await manager.create_session(name="测试会话1")
    print(f"✅ 创建匿名会话成功: {session1.id}")
    print(f"   - 名称: {session1.name}")
    print(f"   - 用户ID: {session1.user_id}")
    print(f"   - 状态: {session1.status}")
    
    # 2. 测试创建用户会话
    print("\n2. 测试创建用户会话...")
    session2 = await manager.create_session(
        user_id="test_user_123",
        name="测试用户会话"
    )
    print(f"✅ 创建用户会话成功: {session2.id}")
    print(f"   - 名称: {session2.name}")
    print(f"   - 用户ID: {session2.user_id}")
    
    # 3. 测试获取会话
    print("\n3. 测试获取会话...")
    retrieved = await manager.get_session(session1.id)
    print(f"✅ 获取匿名会话成功: {retrieved.name}")
    
    retrieved_user = await manager.get_session(session2.id, user_id="test_user_123")
    print(f"✅ 获取用户会话成功: {retrieved_user.name}")
    
    # 4. 测试列出会话
    print("\n4. 测试列出会话...")
    anon_sessions = await manager.list_sessions()
    print(f"✅ 匿名会话列表: {len(anon_sessions)} 个会话")
    
    user_sessions = await manager.list_sessions(user_id="test_user_123")
    print(f"✅ 用户会话列表: {len(user_sessions)} 个会话")
    
    # 5. 测试添加消息
    print("\n5. 测试添加消息...")
    message = ChatMessage(
        id="test_msg_1",
        type=MessageType.USER,
        content="这是一条测试消息",
        is_complete=True
    )
    updated = await manager.add_message_to_session(session1.id, message)
    print(f"✅ 添加消息成功，消息数: {updated.message_count}")
    
    # 6. 测试更新会话
    print("\n6. 测试更新会话...")
    updated = await manager.update_session(
        session1.id,
        name="更新后的会话名称",
        status=SessionStatus.COMPLETED
    )
    print(f"✅ 更新会话成功: {updated.name}, 状态: {updated.status}")
    
    # 7. 测试 Handler 管理
    print("\n7. 测试 Handler 管理...")
    handler = manager.get_handler(session1.id)
    print(f"✅ 获取 Handler 成功: {handler is not None}")
    
    # 8. 测试路径获取
    print("\n8. 测试路径获取...")
    path1 = manager.get_session_path(session1.id)
    path2 = manager.get_session_path(session2.id, user_id="test_user_123")
    print(f"✅ 匿名会话路径: {path1}")
    print(f"✅ 用户会话路径: {path2}")
    
    # 验证路径结构
    assert "anonymous" in str(path1), "匿名会话应该在 anonymous 目录"
    assert "users/test_user_123" in str(path2), "用户会话应该在 users/{user_id} 目录"
    
    # 9. 测试删除会话
    print("\n9. 测试删除会话...")
    success = await manager.delete_session(session1.id)
    print(f"✅ 删除匿名会话: {'成功' if success else '失败'}")
    
    success = await manager.delete_session(session2.id, user_id="test_user_123")
    print(f"✅ 删除用户会话: {'成功' if success else '失败'}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


async def test_profile_manager():
    """测试 ProfileManager 与新架构的集成"""
    print("\n" + "=" * 60)
    print("测试 ProfileManager 集成")
    print("=" * 60)
    
    from profile_manager import ProfileManager
    
    # 1. 测试匿名用户的 ProfileManager
    print("\n1. 测试匿名用户 ProfileManager...")
    pm1 = ProfileManager(session_id="test_profile_anon")
    print(f"✅ 创建匿名 ProfileManager 成功")
    print(f"   - 路径: {pm1.session_path}")
    
    # 2. 测试注册用户的 ProfileManager
    print("\n2. 测试注册用户 ProfileManager...")
    pm2 = ProfileManager(
        session_id="test_profile_user",
        user_id="test_user_456"
    )
    print(f"✅ 创建用户 ProfileManager 成功")
    print(f"   - 路径: {pm2.session_path}")
    
    # 验证路径
    assert "anonymous" in str(pm1.session_path), "匿名 ProfileManager 路径错误"
    assert "users/test_user_456" in str(pm2.session_path), "用户 ProfileManager 路径错误"
    
    # 3. 测试基本功能
    print("\n3. 测试 ProfileManager 基本功能...")
    pm1.append_trait("测试特征1")
    pm1.append_trait("测试特征2")
    profile = pm1.get_full_profile()
    print(f"✅ 档案内容: {len(profile)} 字符")
    
    # 清理
    import shutil
    if pm1.session_path.exists():
        shutil.rmtree(pm1.session_path)
    if pm2.session_path.exists():
        shutil.rmtree(pm2.session_path)
    
    print("\n✅ ProfileManager 集成测试通过！")


async def test_conversation_handler():
    """测试 ConversationHandler 与新架构的集成"""
    print("\n" + "=" * 60)
    print("测试 ConversationHandler 集成")
    print("=" * 60)
    
    from conversation_handler import ConversationHandler
    
    # 1. 测试匿名用户的 ConversationHandler
    print("\n1. 测试匿名 ConversationHandler...")
    handler1 = ConversationHandler(session_id="test_conv_anon")
    print(f"✅ 创建匿名 ConversationHandler 成功")
    print(f"   - ProfileManager 路径: {handler1.profile_manager.session_path}")
    
    # 2. 测试注册用户的 ConversationHandler
    print("\n2. 测试用户 ConversationHandler...")
    handler2 = ConversationHandler(
        session_id="test_conv_user",
        user_id="test_user_789"
    )
    print(f"✅ 创建用户 ConversationHandler 成功")
    print(f"   - ProfileManager 路径: {handler2.profile_manager.session_path}")
    
    # 验证路径
    assert "anonymous" in str(handler1.profile_manager.session_path)
    assert "users/test_user_789" in str(handler2.profile_manager.session_path)
    
    # 清理
    import shutil
    if handler1.profile_manager.session_path.exists():
        shutil.rmtree(handler1.profile_manager.session_path)
    if handler2.profile_manager.session_path.exists():
        shutil.rmtree(handler2.profile_manager.session_path)
    
    print("\n✅ ConversationHandler 集成测试通过！")


async def main():
    """运行所有测试"""
    try:
        await test_session_manager()
        await test_profile_manager()
        await test_conversation_handler()
        
        print("\n" + "🎉" * 30)
        print("🎉 所有重构验证测试通过！架构切换成功！ 🎉")
        print("🎉" * 30)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

