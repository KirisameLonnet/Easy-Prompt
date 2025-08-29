# Easy Prompt - 角色立体化提示词生成工具

一个基于对话驱动的角色立体化提示词生成工具，通过智能对话帮助用户构建丰富、立体的角色档案，并生成高质量的提示词。

## 🌟 项目特性

- 🤖 **智能对话引导**：通过AI对话逐步挖掘角色特征
- 📊 **实时评估反馈**：增强的评估状态显示，包含特性分析、关键词提取和完整度指标
- 🎯 **流式输出**：支持实时流式对话体验
- 🌐 **WebSocket通信**：前后端实时双向通信
- 💻 **现代化前端**：基于Quasar + Vue 3 + TypeScript，响应式设计
- 🐍 **多API支持**：支持 Google Gemini 和 OpenAI 兼容API（OpenAI、Claude、DeepSeek等）
- 🔥 **R18内容模式**：专业的成人内容角色创作支持
- 🔒 **多用户安全**：会话隔离，API配置互不干扰
- 📱 **响应式UI**：增强的评估卡片，支持滚动查看详细信息

## 🏗️ 系统架构

```
easy-prompt/
├── 📁 后端服务 (Python FastAPI + WebSocket)
│   ├── main.py                    # WebSocket服务端点，多用户会话管理
│   ├── conversation_handler.py    # 对话逻辑处理
│   ├── llm_helper.py             # 统一LLM接口封装
│   ├── openai_helper.py          # OpenAI兼容API支持
│   ├── gemini_helper.py          # Google Gemini API支持
│   ├── profile_manager.py        # 角色档案管理
│   ├── evaluator_service.py      # 后台评估服务
│   ├── language_manager.py       # 多语言支持
│   └── session_manager.py        # 会话管理
├── 📁 前端应用 (Quasar + Vue 3 + TypeScript)
│   └── web-client/EasyP-webui/
│       ├── src/
│       │   ├── components/        # Vue组件
│       │   │   ├── EnhancedEvaluationCard.vue  # 增强评估卡片
│       │   │   └── ...
│       │   ├── pages/            # 页面
│       │   ├── services/         # WebSocket服务
│       │   └── types/            # TypeScript类型定义
│       └── ...
├── 📁 配置与文档
│   ├── Document/                 # 开发文档
│   ├── locales/                  # 多语言文件
│   └── requirements.txt          # Python依赖
└── 📁 会话数据
    └── sessions/                 # 动态生成的用户会话目录
        └── {session-id}/
            ├── character_profile.txt
            └── score.json
```

## 🔧 技术栈

### 后端
- **Python 3.8+** - 核心编程语言
- **FastAPI** - 现代、高性能的Web框架
- **WebSocket** - 实时双向通信
- **Google Generative AI** - Gemini API支持
- **OpenAI兼容API** - 支持OpenAI、Claude、DeepSeek等

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Quasar** - Vue.js企业级框架
- **TypeScript** - 类型安全的JavaScript
- **WebSocket** - 实时通信客户端

## 🚀 快速开始

## 🚀 快速开始

### 环境要求
- **Python**: 3.8+
- **Node.js**: 16+
- **API密钥**: Google Gemini API 或 OpenAI兼容API（如DeepSeek、Claude等）

### 部署方式

#### 🎯 方式1：前端配置API（推荐）
无需环境变量配置，在前端界面直接配置API！

#### 🔧 方式2：环境变量配置
如需默认API配置，可设置环境变量。

**⚠️ 注意：前端配置会覆盖环境变量设置**

## 📦 安装部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd easy-prompt
```

### 2. 后端设置

#### Windows:
```cmd
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn main:app --reload
```

#### macOS/Linux:
```bash
# 方式1: 使用Nix (推荐)
nix develop

# 方式2: 传统方式
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动后端
uvicorn main:app --reload
```

### 3. 前端设置

```bash
# 进入前端目录
cd web-client/EasyP-webui

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问应用

- **前端**: http://localhost:9000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## ⚙️ API配置

### 前端配置（推荐）

1. 打开前端应用
2. 点击 **设置** 按钮
3. 选择API类型：
   - **Google Gemini**: 需要Google API Key
   - **OpenAI兼容**: 支持OpenAI、Claude、DeepSeek等
4. 填入API密钥和相关配置
5. 点击 **保存配置** 开始使用

### 支持的API提供商

| 提供商 | API类型 | Base URL | 推荐模型 | 说明 |
|--------|---------|----------|----------|------|
| Google Gemini | `gemini` | - | `gemini-2.5-flash` | Google官方模型 |
| OpenAI | `openai` | `https://api.openai.com/v1` | `gpt-4`, `gpt-3.5-turbo` | OpenAI官方 |
| DeepSeek | `openai` | `https://api.deepseek.com/v1` | `deepseek-chat` | 性价比推荐 |
| Claude (Anthropic) | `openai` | 通过代理 | `claude-3-sonnet` | 通过OpenAI兼容接口 |

### 环境变量配置（可选）

如需设置默认API配置，可创建以下环境变量：

#### OpenAI兼容API（推荐）
```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"  # 可选，默认DeepSeek
export OPENAI_MODEL="deepseek-chat"                   # 可选
export OPENAI_TEMPERATURE="0.7"                       # 可选
export OPENAI_MAX_TOKENS="4000"                       # 可选
export NSFW_MODE="false"                               # 可选，R18模式
```

#### Google Gemini API
```bash
export GOOGLE_API_KEY="your_google_api_key"
export GEMINI_MODEL="gemini-2.5-flash"                # 可选
export EVALUATOR_MODEL="gemini-2.5-flash"             # 可选
export NSFW_MODE="false"                               # 可选，R18模式
```

## 🎨 功能特性

### R18内容模式
- 专业的成人内容角色创作支持
- 增强的R18提示词工程
- 安全的内容过滤机制

### 增强的评估系统
- **实时特性提取**: 自动识别角色特征
- **关键词分析**: 智能提取相关关键词  
- **完整度指标**: 多维度评估角色完善程度
- **可视化评分**: 直观的圆形进度图表
- **滚动式详情**: 响应式卡片设计

### 多API支持
- **自动检测**: 智能识别可用的API配置
- **实时切换**: 会话中随时更改API设置
- **会话隔离**: 多用户API配置互不干扰
- **故障转移**: API失败时自动提示

# 安装前端依赖
npm install

# 启动开发服务器
npm run dev
```

## 环境变量配置

**⚠️ 重要：开始开发前必须正确配置环境变量**

### 多API支持
- **自动检测**: 智能识别可用的API配置
- **实时切换**: 会话中随时更改API设置
- **会话隔离**: 多用户API配置互不干扰
- **故障转移**: API失败时自动提示

## 📖 使用指南

### 基本使用流程

1. **启动应用**
   - 后端：`uvicorn main:app --reload`
   - 前端：`npm run dev`
   - 访问：http://localhost:9000

2. **配置API**
   - 点击 **设置** 按钮
   - 选择API类型（Gemini 或 OpenAI兼容）
   - 填入API密钥和配置
   - 保存并开始使用

3. **创建角色**
   - 与AI开始对话
   - 描述角色的基本信息
   - 跟随AI的引导问题逐步完善

4. **实时评估**
   - 右侧评估卡片显示实时分析
   - 查看已提取的特性和关键词
   - 监控角色完整度指标

5. **生成最终提示词**
   - 当评估达到要求时，AI会询问是否生成
   - 确认后获得专业的角色扮演提示词

### 高级功能

#### R18内容模式
- 在API配置中启用R18模式
- 专业创作成人内容角色
- 增强的提示词和安全设置

#### 多用户支持
- 每个用户独立的会话空间
- API配置互不干扰
- 安全的数据隔离

## 🛠️ 开发指南

### 后端开发

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 启动开发服务器（支持热重载）
uvicorn main:app --reload

# 查看API文档
# http://localhost:8000/docs
```

### 前端开发

```bash
cd web-client/EasyP-webui

# 开发模式（热重载）
npm run dev

# 构建生产版本
npm run build

# 类型检查
npm run lint

# 代码格式化
npm run format
```

### 项目结构

```
easy-prompt/
├── 📁 CopilotFile/              # 测试文件和总结
├── 📁 Document/                 # 开发文档
│   ├── DEV_DOC.md              # 详细开发文档
│   ├── WEBSOCKET_API.md        # WebSocket API文档
│   └── ...
├── 📁 locales/zh/              # 多语言支持
├── 📁 sessions/                # 用户会话数据（运行时生成）
└── 📁 web-client/EasyP-webui/  # 前端应用
```

## 🚨 常见问题

### API配置问题

**Q: API配置失败怎么办？**
A: 
1. 检查API密钥是否正确
2. 确认网络连接
3. 查看浏览器开发者工具的错误信息
4. 尝试切换不同的API提供商

**Q: 为什么两个人同时使用会有冲突？**
A: 
- Gemini API存在全局配置冲突，建议使用OpenAI兼容API
- 系统已添加API配置锁来减少冲突
- 推荐生产环境使用DeepSeek等OpenAI兼容API

### 功能使用问题

**Q: 为什么AI一直在问问题，不生成最终提示词？**
A: 系统会根据角色丰富度自动判断。角色信息越详细，越容易触发最终生成。

**Q: 如何启用R18模式？**
A: 在API配置中启用"R18内容模式"开关，系统会使用专门的成人内容提示词。

**Q: 生成的角色档案保存在哪里？**
A: 保存在项目的 `sessions/` 目录下，每个会话都有独立的文件夹。

## 📚 相关文档

- [开发文档](Document/DEV_DOC.md) - 详细的技术文档
- [WebSocket API](Document/WEBSOCKET_API.md) - API接口文档
- [评估重构总结](CopilotFile/EVALUATION_REFACTOR_SUMMARY.md) - 最新功能说明

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
