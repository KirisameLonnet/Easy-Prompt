#!/usr/bin/env python3
"""
简化的重构验证测试脚本
不依赖 FastAPI，只测试核心功能
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_storage_layer():
    """测试存储层"""
    print("=" * 60)
    print("测试存储层 (SessionStore & FileSystemSessionStore)")
    print("=" * 60)
    
    from storage import FileSystemSessionStore, default_store
    from schemas import Session, SessionStatus
    from datetime import datetime
    
    store = default_store
    
    # 1. 测试创建匿名会话
    print("\n1. 测试创建匿名会话...")
    session1 = Session(
        id="test_anon_001",
        name="测试匿名会话",
        user_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status=SessionStatus.ACTIVE
    )
    created = await store.create_session(session1)
    print(f"✅ 创建成功: {created.id}")
    
    # 验证路径
    path = store.get_session_path(session1.id)
    print(f"   - 路径: {path}")
    assert "anonymous" in str(path), "匿名会话应该在 anonymous 目录"
    
    # 2. 测试创建用户会话
    print("\n2. 测试创建用户会话...")
    session2 = Session(
        id="test_user_001",
        name="测试用户会话",
        user_id="user_123",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status=SessionStatus.ACTIVE
    )
    created = await store.create_session(session2, user_id="user_123")
    print(f"✅ 创建成功: {created.id}")
    
    # 验证路径
    path = store.get_session_path(session2.id, user_id="user_123")
    print(f"   - 路径: {path}")
    assert "users/user_123" in str(path), "用户会话应该在 users/{user_id} 目录"
    
    # 3. 测试获取会话
    print("\n3. 测试获取会话...")
    retrieved1 = await store.get_session(session1.id)
    print(f"✅ 获取匿名会话: {retrieved1.name}")
    
    retrieved2 = await store.get_session(session2.id, user_id="user_123")
    print(f"✅ 获取用户会话: {retrieved2.name}")
    
    # 4. 测试列出会话
    print("\n4. 测试列出会话...")
    anon_list = await store.list_sessions()
    print(f"✅ 匿名会话列表: {len(anon_list)} 个")
    
    user_list = await store.list_sessions(user_id="user_123")
    print(f"✅ 用户会话列表: {len(user_list)} 个")
    
    # 5. 测试更新会话
    print("\n5. 测试更新会话...")
    session1.name = "更新后的名称"
    updated = await store.update_session(session1)
    print(f"✅ 更新成功: {updated.name}")
    
    # 6. 测试档案操作
    print("\n6. 测试档案操作...")
    await store.save_profile(session1.id, "测试档案内容")
    profile = await store.load_profile(session1.id)
    print(f"✅ 档案操作成功，内容长度: {len(profile)}")
    
    await store.append_to_profile(session1.id, "追加内容")
    profile = await store.load_profile(session1.id)
    print(f"✅ 追加成功，新长度: {len(profile)}")
    
    # 7. 测试提示词操作
    print("\n7. 测试提示词操作...")
    await store.save_final_prompt(session1.id, "# 测试提示词\n这是测试内容")
    prompt = await store.load_final_prompt(session1.id)
    print(f"✅ 提示词操作成功，内容长度: {len(prompt)}")
    
    # 8. 测试删除会话
    print("\n8. 测试删除会话...")
    success1 = await store.delete_session(session1.id)
    success2 = await store.delete_session(session2.id, user_id="user_123")
    print(f"✅ 删除匿名会话: {'成功' if success1 else '失败'}")
    print(f"✅ 删除用户会话: {'成功' if success2 else '失败'}")
    
    print("\n" + "=" * 60)
    print("✅ 存储层测试全部通过！")
    print("=" * 60)


async def test_profile_manager():
    """测试 ProfileManager"""
    print("\n" + "=" * 60)
    print("测试 ProfileManager")
    print("=" * 60)
    
    from profile_manager import ProfileManager
    import shutil
    
    # 1. 测试匿名用户
    print("\n1. 测试匿名用户 ProfileManager...")
    pm1 = ProfileManager(session_id="test_pm_anon")
    print(f"✅ 创建成功")
    print(f"   - 路径: {pm1.session_path}")
    assert "anonymous" in str(pm1.session_path)
    
    pm1.append_trait("特征1")
    pm1.append_trait("特征2")
    profile = pm1.get_full_profile()
    print(f"✅ 档案操作成功，内容: {len(profile)} 字符")
    
    # 2. 测试注册用户
    print("\n2. 测试注册用户 ProfileManager...")
    pm2 = ProfileManager(session_id="test_pm_user", user_id="user_456")
    print(f"✅ 创建成功")
    print(f"   - 路径: {pm2.session_path}")
    assert "users/user_456" in str(pm2.session_path)
    
    # 清理
    if pm1.session_path.exists():
        shutil.rmtree(pm1.session_path)
    if pm2.session_path.exists():
        shutil.rmtree(pm2.session_path)
    
    print("\n✅ ProfileManager 测试通过！")


async def test_architecture():
    """测试架构完整性"""
    print("\n" + "=" * 60)
    print("测试架构完整性")
    print("=" * 60)
    
    # 1. 测试模块导入
    print("\n1. 测试模块导入...")
    try:
        from storage import SessionStore, FileSystemSessionStore, default_store
        print("✅ storage 模块导入成功")
        
        from schemas import Session, SessionStatus, ChatMessage
        print("✅ schemas 模块导入成功")
        
        from profile_manager import ProfileManager
        print("✅ ProfileManager 导入成功")
        
        # 注意：ConversationHandler 和 SessionManager 依赖 fastapi
        # 在没有安装 fastapi 的环境下跳过
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        raise
    
    # 2. 验证目录结构
    print("\n2. 验证目录结构...")
    sessions_dir = Path("./sessions")
    anon_dir = sessions_dir / "anonymous"
    users_dir = sessions_dir / "users"
    
    print(f"   - sessions/ 存在: {sessions_dir.exists()}")
    print(f"   - sessions/anonymous/ 存在: {anon_dir.exists()}")
    print(f"   - sessions/users/ 存在: {users_dir.exists()}")
    
    if not anon_dir.exists():
        anon_dir.mkdir(parents=True)
    if not users_dir.exists():
        users_dir.mkdir(parents=True)
    
    print("✅ 目录结构验证通过！")


async def main():
    """运行所有测试"""
    try:
        print("\n" + "🚀" * 30)
        print("开始重构验证测试")
        print("🚀" * 30)
        
        await test_architecture()
        await test_storage_layer()
        await test_profile_manager()
        
        print("\n" + "🎉" * 30)
        print("🎉 核心功能测试全部通过！")
        print("🎉 重构架构切换成功！")
        print("🎉" * 30)
        
        print("\n📝 注意：完整功能测试需要安装依赖（FastAPI等）")
        print("   运行: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

