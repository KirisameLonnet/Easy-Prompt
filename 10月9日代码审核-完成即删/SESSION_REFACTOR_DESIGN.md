# 会话管理系统重构设计

## 当前问题分析

### 1. 架构问题
- **文件存储耦合**：SessionService和ProfileManager都直接操作文件系统
- **缺少用户概念**：所有session在同一个目录下，没有用户隔离
- **路径硬编码**：`./sessions` 路径在多处硬编码
- **职责不清**：SessionService既管理session元数据，又管理文件存储

### 2. 未来扩展需求
- 支持多用户
- 用户身份验证
- 用户间session隔离
- 可能的云存储支持（本地/云端切换）
- session共享和权限管理

## 重构设计方案

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Application Layer                     │
│  (main.py, routes, WebSocket handlers)                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    SessionManager                            │
│  • 会话生命周期管理                                          │
│  • 会话状态管理                                              │
│  • 用户会话隔离 (user_id支持)                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
       ┌───────────┼───────────┐
       │           │           │
┌──────▼──────┐ ┌─▼─────────┐ ┌▼──────────────┐
│SessionStore │ │ Handler   │ │ UserService   │
│  (抽象层)   │ │ Manager   │ │  (未来)       │
└──────┬──────┘ └───────────┘ └───────────────┘
       │
       │ implements
       │
┌──────▼──────────────────┐
│ FileSystemSessionStore  │  (当前实现)
│ • 本地文件存储          │
│ • 按用户ID分目录        │
└─────────────────────────┘
       │
       │ future: 可替换为
       │
┌──────▼──────────────────┐
│   DatabaseSessionStore  │  (未来实现)
│ • 数据库存储            │
│ • SQL/NoSQL支持         │
└─────────────────────────┘
```

### 核心组件设计

#### 1. SessionStore (抽象存储层)
```python
from abc import ABC, abstractmethod

class SessionStore(ABC):
    """会话存储抽象接口"""
    
    @abstractmethod
    async def create(self, session: Session, user_id: Optional[str] = None) -> Session:
        """创建会话"""
        pass
    
    @abstractmethod
    async def get(self, session_id: str, user_id: Optional[str] = None) -> Optional[Session]:
        """获取会话"""
        pass
    
    @abstractmethod
    async def list(self, user_id: Optional[str] = None, limit: int = 50) -> List[Session]:
        """列出会话"""
        pass
    
    @abstractmethod
    async def update(self, session: Session, user_id: Optional[str] = None) -> Session:
        """更新会话"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """删除会话"""
        pass
    
    @abstractmethod
    async def save_profile(self, session_id: str, profile_data: str, user_id: Optional[str] = None):
        """保存角色档案"""
        pass
    
    @abstractmethod
    async def load_profile(self, session_id: str, user_id: Optional[str] = None) -> str:
        """加载角色档案"""
        pass
```

#### 2. FileSystemSessionStore (当前实现)
```python
class FileSystemSessionStore(SessionStore):
    """基于文件系统的会话存储"""
    
    def __init__(self, base_path: str = "./sessions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def _get_user_dir(self, user_id: Optional[str] = None) -> Path:
        """获取用户目录"""
        if user_id:
            # 有用户ID：sessions/users/{user_id}/
            user_dir = self.base_path / "users" / user_id
        else:
            # 无用户ID（匿名）：sessions/anonymous/
            user_dir = self.base_path / "anonymous"
        
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_session_dir(self, session_id: str, user_id: Optional[str] = None) -> Path:
        """获取会话目录"""
        return self._get_user_dir(user_id) / session_id
    
    async def create(self, session: Session, user_id: Optional[str] = None) -> Session:
        # 实现...
        pass
```

#### 3. SessionManager (统一管理层)
```python
class SessionManager:
    """
    会话管理器 - 统一的会话管理接口
    支持用户隔离，为未来的多用户系统做准备
    """
    
    def __init__(self, store: SessionStore):
        self.store = store
        self.active_handlers: Dict[str, ConversationHandler] = {}
    
    async def create_session(
        self,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs
    ) -> Session:
        """创建会话（支持用户ID）"""
        session_id = str(uuid.uuid4())
        
        if not name:
            now = datetime.now()
            name = f"会话 {now.strftime('%Y-%m-%d %H:%M')}"
        
        session = Session(
            id=session_id,
            name=name,
            user_id=user_id,  # 新增：关联用户
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SessionStatus.ACTIVE
        )
        
        # 通过存储层创建
        session = await self.store.create(session, user_id)
        
        # 创建handler
        handler = ConversationHandler(
            session_id=session_id,
            user_id=user_id
        )
        self.active_handlers[session_id] = handler
        
        return session
    
    async def get_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Session]:
        """获取会话（验证用户权限）"""
        session = await self.store.get(session_id, user_id)
        
        # 如果指定了user_id，验证会话所有权
        if session and user_id and session.user_id != user_id:
            raise PermissionError(f"User {user_id} has no access to session {session_id}")
        
        return session
    
    async def list_user_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Session]:
        """列出用户的所有会话"""
        return await self.store.list(user_id, limit)
```

### 数据模型更新

#### Session Schema
```python
class Session(BaseModel):
    """会话模型"""
    id: str
    name: str
    user_id: Optional[str] = None  # 新增：关联用户ID
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    last_message: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    evaluation_data: Optional[EvaluationData] = None
    
    # 新增：访问控制相关
    is_public: bool = False  # 是否公开（未来可用于分享）
    shared_with: List[str] = Field(default_factory=list)  # 共享给哪些用户
```

### 目录结构

#### 当前结构
```
sessions/
  ├── {session-id-1}/
  │   ├── session.json
  │   ├── character_profile.txt
  │   └── final_prompt.md
  └── {session-id-2}/
      └── ...
```

#### 重构后结构（支持多用户）
```
sessions/
  ├── anonymous/              # 匿名用户（未登录）
  │   ├── {session-id-1}/
  │   │   ├── session.json
  │   │   ├── character_profile.txt
  │   │   └── final_prompt.md
  │   └── {session-id-2}/
  │       └── ...
  └── users/                  # 注册用户
      ├── {user-id-1}/
      │   ├── {session-id-a}/
      │   │   └── ...
      │   └── {session-id-b}/
      │       └── ...
      └── {user-id-2}/
          └── ...
```

### 迁移策略

#### Phase 1: 抽象层引入（当前阶段）
1. 创建 `SessionStore` 抽象接口
2. 实现 `FileSystemSessionStore`
3. 创建新的 `SessionManager`
4. 保持向后兼容，`user_id` 为 `None` 时使用 `anonymous`

#### Phase 2: 数据迁移
1. 将现有 `sessions/` 下的所有session移动到 `sessions/anonymous/`
2. 提供迁移脚本

#### Phase 3: 账号系统集成（未来）
1. 添加 `UserService`
2. 实现身份验证中间件
3. 在WebSocket握手时获取用户信息
4. 所有session操作自动关联用户ID

### 兼容性保证

```python
# 当前代码（无需修改）
session = await session_manager.create_session(name="测试会话")

# 未来代码（自动支持）
session = await session_manager.create_session(
    user_id=current_user.id,
    name="测试会话"
)
```

### API设计

#### REST API
```
GET    /api/sessions                    # 列出当前用户的会话
GET    /api/sessions/{session_id}       # 获取会话详情
POST   /api/sessions                    # 创建会话
PUT    /api/sessions/{session_id}       # 更新会话
DELETE /api/sessions/{session_id}       # 删除会话

# 未来扩展
GET    /api/users/{user_id}/sessions    # 管理员查看用户会话
POST   /api/sessions/{session_id}/share # 分享会话
```

#### WebSocket
```python
# 当前：直接连接
ws://localhost:8000/ws/prompt

# 未来：带认证
ws://localhost:8000/ws/prompt?token={jwt_token}
```

### 配置化

```python
# config.py
class SessionConfig:
    # 存储类型：filesystem, database, s3等
    STORAGE_TYPE: str = "filesystem"
    
    # 文件存储路径
    SESSIONS_PATH: str = "./sessions"
    
    # 是否启用用户隔离
    ENABLE_USER_ISOLATION: bool = False
    
    # 默认用户ID（未登录时使用）
    ANONYMOUS_USER_ID: str = "anonymous"
    
    # 未来：数据库配置
    # DATABASE_URL: str = "postgresql://..."
```

## 实施步骤

### Step 1: 创建抽象层（不破坏现有功能）
- [ ] 创建 `session_store.py` - 定义抽象接口
- [ ] 创建 `filesystem_store.py` - 文件系统实现
- [ ] 创建测试用例

### Step 2: 重构SessionService
- [ ] 将SessionService重命名为SessionManager
- [ ] 注入SessionStore依赖
- [ ] 添加user_id参数（可选）

### Step 3: 更新ProfileManager
- [ ] 接受user_id参数
- [ ] 调整文件路径逻辑

### Step 4: 数据迁移
- [ ] 创建迁移脚本
- [ ] 迁移现有sessions到anonymous目录

### Step 5: 更新API和WebSocket
- [ ] 更新路由以支持用户上下文
- [ ] 保持向后兼容

## 优势

1. **渐进式重构**：不破坏现有功能
2. **职责分离**：存储、管理、业务逻辑清晰分离
3. **易于扩展**：可轻松替换存储后端
4. **用户隔离**：为多用户系统铺路
5. **可测试性**：通过依赖注入，便于单元测试
6. **配置灵活**：支持不同环境的不同配置

## 风险和缓解

| 风险 | 缓解措施 |
|-----|---------|
| 破坏现有功能 | 完整的单元测试和集成测试 |
| 性能下降 | 性能基准测试，必要时优化 |
| 迁移数据丢失 | 迁移前完整备份 |
| 学习曲线 | 详细文档和示例代码 |

