# Easy Prompt - 开发文档

## 📋 目录

1. [项目简介](#1-项目简介)
2. [核心架构](#2-核心架构)
3. [技术栈](#3-技术栈)
4. [开发环境配置](#4-开发环境配置)
5. [项目结构](#5-项目结构)
6. [API支持](#6-api支持)
7. [核心组件详解](#7-核心组件详解)
8. [WebSocket协议](#8-websocket协议)
9. [开发指南](#9-开发指南)
10. [测试指南](#10-测试指南)
11. [部署指南](#11-部署指南)
12. [故障排除](#12-故障排除)

## 1. 项目简介

Easy Prompt 是一个智能的角色扮演提示词生成工具，通过AI驱动的对话帮助用户构建丰富、立体的角色档案。项目采用前后端分离架构，支持多种AI API，提供流式实时对话体验。

### 主要特性

- 🤖 **多AI支持**：支持Google Gemini、OpenAI、Claude、DeepSeek等API
- 💬 **智能对话**：通过引导性对话挖掘角色特征
- 📊 **实时评估**：异步评估角色档案完整度
- 🌊 **流式输出**：支持实时流式对话体验
- 🔌 **WebSocket通信**：前后端实时双向通信
- 🎨 **现代前端**：基于Quasar + Vue 3 + TypeScript
- 🐍 **Python后端**：FastAPI + 多种LLM API支持

## 2. 核心架构

### 2.1 系统架构图

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   前端 (Vue3)   │ ←────────────→ │  后端 (FastAPI) │
│                 │                 │                 │
│ ┌─────────────┐ │                 │ ┌─────────────┐ │
│ │ API配置组件 │ │                 │ │ API管理器   │ │
│ └─────────────┘ │                 │ └─────────────┘ │
│ ┌─────────────┐ │                 │ ┌─────────────┐ │
│ │ 对话组件    │ │                 │ │ 对话处理器  │ │
│ └─────────────┘ │                 │ └─────────────┘ │
│ ┌─────────────┐ │                 │ ┌─────────────┐ │
│ │ 评估组件    │ │                 │ │ 评估服务    │ │
│ └─────────────┘ │                 │ └─────────────┘ │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │                                   │
    ┌─────────┐                       ┌─────────────┐
    │ 本地存储 │                       │ 会话管理器  │
    └─────────┘                       └─────────────┘
                                             │
                                    ┌─────────────────┐
                                    │ 多AI适配层      │
                                    │ ┌─────────────┐ │
                                    │ │ Gemini API  │ │
                                    │ │ OpenAI API  │ │
                                    │ │ Claude API  │ │
                                    │ │ DeepSeek API│ │
                                    │ └─────────────┘ │
                                    └─────────────────┘
```

### 2.2 核心服务

#### 2.2.1 对话服务 (ConversationHandler)
- **职责**：与用户进行引导性对话，提取角色特征
- **输入**：用户消息、评估反馈
- **输出**：AI回复、提取的角色特征

#### 2.2.2 评估服务 (EvaluatorService)
- **职责**：异步评估角色档案完整度
- **机制**：文件监控 + 后台评估
- **输出**：评分和改进建议

#### 2.2.3 API管理器 (LLMHelper + OpenAIHelper)
- **职责**：统一管理多种AI API
- **支持**：Google Gemini、OpenAI兼容API
- **特性**：自动切换、错误处理、流式支持

## 3. 技术栈

### 后端技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 🐍 Web框架 | FastAPI | Latest | API服务、WebSocket支持 |
| 🔥 ASGI服务器 | Uvicorn | Latest | 高性能异步服务器 |
| 🤖 AI接口 | google-generativeai | Latest | Google Gemini API |
| 🌐 HTTP客户端 | requests | Latest | OpenAI兼容API调用 |
| 👀 文件监控 | watchdog | Latest | 监控文件变化 |
| 💬 CLI交互 | prompt-toolkit | Latest | 命令行界面 |
| 🔧 环境管理 | python-dotenv | Latest | 环境变量管理 |

### 前端技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| ⚡ 框架 | Vue 3 | 3.4.18 | 响应式前端框架 |
| 🎨 UI框架 | Quasar | 2.16.0 | 组件库和构建工具 |
| 📝 类型系统 | TypeScript | 5.5.3 | 类型安全 |
| 🔌 状态管理 | Composition API | - | 响应式状态管理 |
| 🌐 通信 | WebSocket | - | 实时双向通信 |
| 🏗️ 构建工具 | Vite | - | 快速构建和热重载 |

## 4. 开发环境配置

### 4.1 系统要求

- **Python**: 3.8+
- **Node.js**: 16+
- **NPM/Yarn**: 最新版本
- **Git**: 版本控制

### 4.2 环境配置

#### 4.2.1 克隆项目

```bash
git clone https://github.com/KirisameLonnet/Easy-Prompt.git
cd easy-prompt
```

#### 4.2.2 Python环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 4.2.3 Node.js环境

```bash
cd web-client/EasyP-webui
npm install
```

#### 4.2.4 环境变量配置

创建 `env/` 目录并配置环境变量：

```bash
mkdir env
```

必需的环境变量文件：

**`env/GOOGLE_API_KEY`** (可选，如果使用Gemini)
```
your-google-api-key-here
```

**`env/GEMINI_MODEL`** (可选)
```
gemini-2.5-flash
```

**`env/EVALUATOR_MODEL`** (可选)
```
gemini-2.5-flash
```

**`env/SCORE_THRESHOLD`** (可选)
```
8
```

### 4.3 开发工具配置

#### VS Code 扩展推荐

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "Vue.volar",
    "esbenp.prettier-vscode"
  ]
}
```

## 5. 项目结构

```
easy-prompt/
├── 🐍 后端服务
│   ├── main.py                    # FastAPI主应用
│   ├── conversation_handler.py    # 对话处理逻辑
│   ├── llm_helper.py             # Gemini API封装
│   ├── openai_helper.py          # OpenAI兼容API封装
│   ├── profile_manager.py        # 角色档案管理
│   ├── evaluator_service.py      # 异步评估服务
│   ├── session_manager.py        # 会话管理
│   ├── language_manager.py       # 多语言支持
│   ├── search_helper.py          # 搜索功能
│   ├── requirements.txt          # Python依赖
│   ├── test_*.py                 # 测试文件
│   └── env/                      # 环境变量目录
│       ├── GOOGLE_API_KEY
│       ├── GEMINI_MODEL
│       └── ...
│
├── 🌐 前端应用
│   └── web-client/EasyP-webui/
│       ├── src/
│       │   ├── components/       # Vue组件
│       │   │   ├── ApiConfigDialog.vue    # API配置
│       │   │   ├── ChatInput.vue          # 聊天输入
│       │   │   ├── ChatMessage.vue        # 聊天消息
│       │   │   ├── DebugPanel.vue         # 调试面板
│       │   │   ├── EvaluationCard.vue     # 评估卡片
│       │   │   └── PromptResult.vue       # 结果展示
│       │   ├── services/         # 服务层
│       │   │   └── websocket.ts           # WebSocket服务
│       │   ├── types/            # TypeScript类型
│       │   │   └── websocket.ts           # WebSocket类型定义
│       │   ├── pages/            # 页面组件
│       │   │   └── IndexPage.vue          # 主页面
│       │   └── layouts/          # 布局组件
│       ├── package.json          # 前端依赖
│       └── quasar.config.ts     # Quasar配置
│
├── 📁 会话数据
│   └── sessions/                 # 动态生成的会话目录
│       └── {session-id}/
│           ├── character_profile.txt      # 角色档案
│           ├── score.json                 # 评估分数
│           └── final_prompt.md            # 最终提示词
│
├── 🌍 多语言支持
│   └── locales/
│       └── zh/
│           ├── static_text.json           # 静态文本
│           └── system_prompts.py          # 系统提示词
│
└── 📚 文档
    ├── README.md                 # 项目说明
    ├── DEV_DOC.md               # 开发文档（本文件）
    ├── WEBSOCKET_API.md         # WebSocket API文档
    └── *.md                     # 其他文档
```

## 6. API支持

### 6.1 支持的AI API

| API提供商 | 模型示例 | 默认Base URL | 状态 |
|-----------|----------|--------------|------|
| 🟢 DeepSeek | deepseek-chat | https://api.deepseek.com/v1 | 默认推荐 |
| 🟢 OpenAI | gpt-3.5-turbo, gpt-4 | https://api.openai.com/v1 | 完全支持 |
| 🟢 Google Gemini | gemini-2.5-flash | - | 完全支持 |
| 🟡 Claude | claude-3-sonnet-20240229 | https://api.anthropic.com/v1 | 兼容支持 |
| 🟡 Moonshot | moonshot-v1-8k | https://api.moonshot.cn/v1 | 兼容支持 |

### 6.2 API配置

#### 前端配置界面
用户可以通过前端的API配置对话框进行配置：
- 选择API类型（Gemini/OpenAI兼容）
- 输入API密钥
- 配置Base URL和模型名称
- 调整temperature和max_tokens参数

#### 后端API切换
后端支持运行时切换API，通过WebSocket消息进行配置。

## 7. 核心组件详解

### 7.1 ConversationHandler (对话处理器)

```python
class ConversationHandler:
    """核心对话处理类"""
    
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.chat_session = llm_helper.start_chat_session()
    
    def handle_message(self, user_message: str):
        """处理用户消息的核心方法"""
        # 1. 获取当前评估状态
        critique = self.get_current_critique()
        
        # 2. 调用LLM获取响应流
        response_stream = llm_helper.get_conversation_response_stream(
            self.chat_session, user_message, critique
        )
        
        # 3. 处理流式响应
        for chunk in response_stream:
            yield chunk
```

**关键特性：**
- 流式响应处理
- 评估状态集成
- 多轮对话管理
- 角色特征提取

### 7.2 LLM Helper (AI接口管理)

#### 7.2.1 统一接口设计

```python
# 支持多种API的统一接口
def init_llm(nsfw_mode=False, api_type="gemini", **kwargs):
    """初始化LLM，支持多种API类型"""
    if api_type == "openai":
        return init_openai_llm(**kwargs)
    else:
        return init_gemini_llm(nsfw_mode)

def get_conversation_response_stream(chat_session, user_message, critique):
    """获取对话响应流，自动根据当前API类型路由"""
    if current_api_type == "openai":
        return get_openai_conversation_response_stream(...)
    else:
        return get_gemini_conversation_response_stream(...)
```

#### 7.2.2 OpenAI兼容层

```python
class OpenAIHelper:
    """OpenAI兼容API封装"""
    
    @staticmethod
    def _make_openai_request(messages, stream=False):
        """发送OpenAI格式请求"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        response = requests.post(url, headers=headers, 
                               json=payload, stream=stream)
        return response
```

### 7.3 WebSocket服务

#### 7.3.1 前端WebSocket服务

```typescript
class WebSocketService {
  private ws: WebSocket | null = null;
  private apiConfig: ApiConfig | null = null;
  
  // 连接管理
  connect(): void {
    this.ws = new WebSocket(this.websocketUrl);
    this.setupEventListeners();
  }
  
  // API配置管理
  reconfigureApi(config: ApiConfig): void {
    this.setApiConfig(config);
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.sendApiConfig();
    }
  }
  
  // 消息处理
  private handleMessage(message: WebSocketMessage): void {
    if (isApiConfigResult(message)) {
      this.handleApiConfigResult(message.payload);
    } else if (isAIResponseChunk(message)) {
      this.handleAIResponseChunk(message.payload.chunk);
    }
    // ... 其他消息类型处理
  }
}
```

#### 7.3.2 后端WebSocket端点

```python
@app.websocket("/ws/prompt")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # 1. 等待API配置或使用默认配置
    api_initialized = False
    while not api_initialized:
        data = await websocket.receive_text()
        message = json.loads(data)
        
        if message["type"] == "api_config":
            # 配置API
            if initialize_api(message["payload"]):
                await send_json(websocket, "api_config_result", 
                              {"success": True})
                api_initialized = True
        elif message["type"] == "start_session":
            # 使用默认配置
            if initialize_api(current_api_config):
                api_initialized = True
    
    # 2. 创建对话处理器并开始对话
    handler = ConversationHandler()
    # ... 对话循环
```

## 8. WebSocket协议

### 8.1 消息类型

#### 客户端 → 服务器

| 消息类型 | 用途 | Payload示例 |
|----------|------|-------------|
| `api_config` | 配置API | `{"api_type": "openai", "api_key": "sk-xxx", ...}` |
| `start_session` | 启动默认会话 | `{}` |
| `user_response` | 用户消息 | `{"answer": "我想创建一个魔法师角色"}` |
| `user_confirmation` | 用户确认 | `{"confirm": true}` |

#### 服务器 → 客户端

| 消息类型 | 用途 | Payload示例 |
|----------|------|-------------|
| `api_config_result` | API配置结果 | `{"success": true, "message": "配置成功"}` |
| `system_message` | 系统消息 | `{"message": "请描述角色的基本信息"}` |
| `ai_response_chunk` | AI响应片段 | `{"chunk": "这个角色很有趣"}` |
| `evaluation_update` | 评估更新 | `{"message": "评估中...", "is_ready": false}` |
| `confirmation_request` | 确认请求 | `{"reason": "角色已完善，生成最终提示词？"}` |
| `final_prompt_chunk` | 最终提示词片段 | `{"chunk": "# 角色设定

"}` |
| `session_end` | 会话结束 | `{"message": "感谢使用！"}` |
| `error` | 错误消息 | `{"message": "API配置错误"}` |

### 8.2 消息流程

```
客户端                    服务器
   │                        │
   ├─ api_config ──────────→│
   │                        ├─ 初始化API
   │← api_config_result ────│
   │                        │
   ├─ user_response ────────→│
   │                        ├─ 处理消息
   │← ai_response_chunk ────│ (流式)
   │← ai_response_chunk ────│
   │← evaluation_update ────│
   │                        │
   ├─ user_response ────────→│
   │← confirmation_request ──│
   │                        │
   ├─ user_confirmation ────→│
   │← final_prompt_chunk ───│ (流式)
   │← session_end ──────────│
```

## 9. 开发指南

### 9.1 启动开发环境

#### 9.1.1 启动后端服务

```bash
# 激活Python环境
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 9.1.2 启动前端服务

```bash
cd web-client/EasyP-webui
npm run dev
```

访问：
- 前端应用：http://localhost:9000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 9.2 代码规范

#### 9.2.1 Python代码规范

```python
# 使用类型注解
def handle_message(self, user_message: str) -> Generator[str, None, None]:
    """处理用户消息
    
    Args:
        user_message: 用户输入的消息
        
    Yields:
        str: AI响应的文本片段
    """
    pass

# 使用docstring
class ConversationHandler:
    """对话处理器
    
    负责管理用户与AI之间的对话流程，包括：
    - 消息处理
    - 角色特征提取
    - 评估状态管理
    """
    pass

# 错误处理
try:
    response = api_call()
except APIError as e:
    logger.error(f"API调用失败: {e}")
    yield f"抱歉，服务暂时不可用: {e}"
```

#### 9.2.2 TypeScript代码规范

```typescript
// 使用严格类型
interface ApiConfig {
  api_type: 'gemini' | 'openai';
  api_key: string;
  base_url: string;
  model: string;
  temperature: number;
  max_tokens: number;
}

// 使用类型守卫
function isApiConfigResult(message: WebSocketMessage): message is ApiConfigResult {
  return message.type === 'api_config_result';
}

// 错误处理
try {
  await websocketService.connect();
} catch (error: unknown) {
  console.error('连接失败:', (error as Error).message);
}
```

### 9.3 添加新功能

#### 9.3.1 添加新的AI API支持

1. **创建API适配器**

```python
# new_api_helper.py
def init_new_api_llm(api_key: str, model: str):
    """初始化新API"""
    pass

def get_new_api_conversation_response_stream(messages: list):
    """获取对话响应流"""
    pass
```

2. **集成到LLM Helper**

```python
# llm_helper.py
from new_api_helper import init_new_api_llm

def init_llm(api_type="gemini", **kwargs):
    if api_type == "new_api":
        return init_new_api_llm(**kwargs)
    # ... 其他API类型
```

3. **更新前端配置**

```typescript
// ApiConfigDialog.vue
const presets: ApiPreset[] = [
  {
    name: 'NewAPI',
    base_url: 'https://api.newprovider.com/v1',
    model: 'new-model-name',
    description: 'New API Provider'
  },
  // ... 其他预设
];
```

#### 9.3.2 添加新的WebSocket消息类型

1. **定义类型**

```typescript
// types/websocket.ts
export interface NewMessageType {
  type: 'new_message_type';
  payload: {
    data: string;
  };
}
```

2. **添加到联合类型**

```typescript
export type ServerMessage = 
  | SystemMessage
  | NewMessageType
  | ... // 其他消息类型
```

3. **添加类型守卫**

```typescript
export function isNewMessageType(message: WebSocketMessage): message is NewMessageType {
  return message.type === 'new_message_type';
}
```

4. **处理消息**

```typescript
// services/websocket.ts
private handleMessage(message: WebSocketMessage): void {
  if (isNewMessageType(message)) {
    this.handleNewMessageType(message.payload);
  }
  // ... 其他消息处理
}
```

## 10. 测试指南

### 10.1 后端测试

#### 10.1.1 单元测试

```python
# test_conversation_handler.py
import pytest
from conversation_handler import ConversationHandler

def test_conversation_handler_init():
    """测试对话处理器初始化"""
    handler = ConversationHandler()
    assert handler.profile_manager is not None
    assert handler.chat_session is not None

def test_handle_message():
    """测试消息处理"""
    handler = ConversationHandler()
    response = list(handler.handle_message("测试消息"))
    assert len(response) > 0
```

运行测试：
```bash
python -m pytest test_*.py -v
```

#### 10.1.2 API测试

```python
# test_api_config.py
from llm_helper import init_llm, get_current_api_type

def test_openai_api_config():
    """测试OpenAI API配置"""
    result = init_llm(
        api_type="openai",
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-3.5-turbo"
    )
    assert result == True
    assert get_current_api_type() == "openai"
```

### 10.2 前端测试

#### 10.2.1 组件测试

```bash
cd web-client/EasyP-webui
npm run test
```

#### 10.2.2 E2E测试

使用Cypress进行端到端测试：

```bash
npm run test:e2e
```

### 10.3 集成测试

测试完整的WebSocket通信流程：

```python
# test_websocket_integration.py
import asyncio
import websockets
import json

async def test_websocket_flow():
    """测试WebSocket完整流程"""
    uri = "ws://localhost:8000/ws/prompt"
    
    async with websockets.connect(uri) as websocket:
        # 1. 发送API配置
        config_message = {
            "type": "api_config",
            "payload": {
                "api_type": "openai",
                "api_key": "test-key",
                # ... 其他配置
            }
        }
        await websocket.send(json.dumps(config_message))
        
        # 2. 接收配置结果
        response = await websocket.recv()
        data = json.loads(response)
        assert data["type"] == "api_config_result"
        assert data["payload"]["success"] == True
```

## 11. 部署指南

### 11.1 生产环境部署

#### 11.1.1 Docker部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
docker build -t easy-prompt .
docker run -p 8000:8000 -v $(pwd)/env:/app/env easy-prompt
```

#### 11.1.2 前端部署

```bash
cd web-client/EasyP-webui
npm run build
```

将 `dist/` 目录部署到静态文件服务器。

### 11.2 环境配置

#### 11.2.1 生产环境变量

```bash
# 生产环境配置
export ENVIRONMENT=production
export LOG_LEVEL=info
export API_RATE_LIMIT=100
export MAX_SESSIONS=1000
```

#### 11.2.2 负载均衡

使用Nginx进行负载均衡：

```nginx
upstream easy_prompt_backend {
    server localhost:8000;
    server localhost:8001;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /ws/ {
        proxy_pass http://easy_prompt_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## 12. 故障排除

### 12.1 常见问题

#### 12.1.1 API配置问题

**问题**：API密钥无效
```
错误: OpenAI API请求失败: 401 Unauthorized
```

**解决方案**：
1. 检查API密钥是否正确
2. 确认API密钥有足够的权限
3. 检查API配额是否用完

#### 12.1.2 WebSocket连接问题

**问题**：WebSocket连接失败
```
错误: WebSocket connection failed
```

**解决方案**：
1. 检查后端服务是否运行
2. 确认端口8000是否可访问
3. 检查防火墙设置

#### 12.1.3 前端编译问题

**问题**：TypeScript编译错误
```
错误: Unexpected any. Specify a different type.
```

**解决方案**：
1. 使用具体类型替换any
2. 添加类型注解
3. 使用unknown类型并进行类型断言

### 12.2 调试工具

#### 12.2.1 后端调试

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用调试模式启动
uvicorn main:app --reload --log-level debug
```

#### 12.2.2 前端调试

```typescript
// 启用WebSocket调试
const websocketService = new WebSocketService();
websocketService.enableDebugMode();

// 查看调试日志
console.log(websocketService.getLogs());
```

### 12.3 性能优化

#### 12.3.1 后端优化

```python
# 使用连接池
from asyncio import create_task
from concurrent.futures import ThreadPoolExecutor

# 异步处理评估
async def async_evaluation(profile_data):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor, evaluate_profile, profile_data
        )
    return result
```

#### 12.3.2 前端优化

```typescript
// 使用防抖处理用户输入
import { debounce } from 'lodash-es';

const debouncedSend = debounce((message: string) => {
  websocketService.sendUserResponse(message);
}, 300);

// 虚拟滚动长列表
const virtualScrollOptions = {
  itemSize: 60,
  overscan: 5
};
```

---

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- **GitHub Issues**: [项目Issue页面](https://github.com/KirisameLonnet/Easy-Prompt/issues)
- **文档更新**: 欢迎提交PR改进文档
- **功能建议**: 在Issue中使用`enhancement`标签

---

**最后更新**: 2025年8月14日
**文档版本**: v2.0.0

## 2. 核心架构与理念

本项目采用“生成器-评估器”（Generator-Evaluator）模型，并将对话与评估解耦，通过文件系统事件进行异步通信。

### 2.1. 三大核心服务

1.  **对话服务 (Conversation Service)**:
    -   **角色**: 与用户直接交互的“访谈者”。
    -   **职责**: 保持对话流畅，引导用户描述角色，并从用户的回复中**提取关键的角色特点**。
    -   **实现**: `conversation_handler.py`

2.  **档案服务 (Profile Service)**:
    -   **角色**: 负责记录和存储的“书记员”。
    -   **职责**: 为每个会话管理一个专属的“角色档案”，通常是包含多个文件的目录（如`./sessions/{session_id}/`）。它负责将“对话服务”提取的特点写入`character_profile.txt`，并管理分数文件`score.json`。
    -   **实现**: `profile_manager.py`

3.  **评估服务 (Evaluator Service)**:
    -   **角色**: 在幕后工作的“评判员”。
    -   **职责**: 这是一个**异步后台服务**。它会持续监控所有角色档案文件 (`character_profile.txt`) 的变动。一旦文件更新，它会立即读取全部内容，调用“评判员LLM”进行打分，并将结果（分数和理由）写回对应的`score.json`文件。
    -   **实现**: `evaluator_service.py` (使用 `watchdog` 库)

### 2.2. 三个LLM模型角色

1.  **对话LLM (The Interviewer)**:
    -   **任务**: 专注于引导性对话。接收部分对话历史和用户最新输入，生成启发性的下一个问题。
    -   **输出**: `(回复给用户的话, 提取出的角色特点文本)`

2.  **评判员LLM (The Evaluator)**:
    -   **任务**: 专注于分析和量化。接收完整的角色特点文本，根据预设的评分标准进行评估。
    -   **输出**: `{"score": 7, "reason": "角色已具备核心身份和鲜明个性，但在行为模式上仍需补充。"}`

3.  **作家LLM (The Writer)**:
    -   **任务**: 专注于格式化和润色。接收最终的角色特点文本，将其整理成一份结构清晰、语言优美的Markdown格式Prompt。
    -   **输出**: 最终的RolePlay Prompt。

### 2.3. 数据流与工作流程

1.  用户通过 **CLI** 或 **WebSocket** 发送消息。
2.  **`ConversationHandler`** 接收消息，调用“对话LLM”。
3.  “对话LLM”返回`(回复, 特点)`。
4.  `ConversationHandler` 将**特点**交给 **`ProfileManager`** 写入`character_profile.txt`。
5.  **`EvaluatorService`** (后台) 检测到文件变化，触发“评判员LLM”进行评分，并将结果写入`score.json`。
6.  `ConversationHandler` 将**回复**和从`score.json`中读取的**最新分数**组合后，呈现给用户。
7.  循环继续，直到分数达到阈值。
8.  `ConversationHandler` 调用“作家LLM”生成最终Prompt并结束对话。

## 3. 技术选型

-   **核心框架**: Python 3
-   **Web/API**: FastAPI, Uvicorn
-   **文件监控**: `watchdog`
-   **命令行交互**: `prompt-toolkit`
-   **LLM/Search**: `google-generativeai`
-   **环境管理**: Nix Flakes + direnv + venv

## 4. 项目文件结构 (预期)

```
easy-prompt/
├── main.py             # FastAPI应用入口 (WebSocket)
├── cli.py              # 命令行应用入口 (CLI)
│
├── conversation_handler.py # 核心：对话服务
├── profile_manager.py  # 核心：档案服务
├── evaluator_service.py  # 核心：异步评估服务
│
├── llm_helper.py       # 封装对三个LLM模型的调用
├── system_prompts.py   # 存放所有System Prompt
│
├── requirements.txt
├── DEV_DOC.md
├── flake.nix
├── .envrc
│
└── sessions/           # (动态创建) 存放所有会话的档案
    └── {session_id}/
        ├── character_profile.txt
        └── score.json
```

## 5. 环境与运行

### 5.1. 环境变量 (`env/` 目录下)

-   `GOOGLE_API_KEY`: 你的API密钥。
-   `GEMINI_MODEL`: 对话LLM使用的模型 (默认: `gemini-2.5-flash`)。
-   `EVALUATOR_MODEL`: 评判员LLM使用的模型 (建议使用更快的模型)。
-   `SCORE_THRESHOLD`: 触发最终生成的评分阈值 (默认: `8`)。

### 5.2. 运行

1.  **安装依赖**: `pip install -r requirements.txt`
2.  **启动程序**:
    -   **CLI模式**: `python cli.py`
    -   **WebSocket模式**: `uvicorn main:app --reload`
    -   *程序启动时，`evaluator_service`将自动在后台开始监控。*

## 6. 量化评分标准

“评判员LLM”将根据以下维度对`character_profile.txt`的内容进行0-10分的综合评估：

1.  **核心身份 (2分)**: 是否清晰定义了角色的基本身份、背景和所处环境？
2.  **鲜明个性 (3分)**: 是否有至少2-3个明确且相互关联的性格特质？
3.  **行为模式 (3分)**: 是否有具体的、可供扮演者参考的行为示例？
4.  **内在矛盾/可探索点 (2分)**: 角色是否有内在的矛盾、秘密或目标？
