# Easy Prompt - 角色立体化提示词生成工具

一个基于对话驱动的角色立体化提示词生成工具，通过智能对话帮助用户构建丰富、立体的角色档案，并生成高质量的提示词。

## 项目特性

- 🤖 **智能对话引导**：通过AI对话逐步挖掘角色特征
- 📊 **实时评估反馈**：实时评估角色档案完整度
- 🎯 **流式输出**：支持实时流式对话体验
- 🌐 **WebSocket通信**：前后端实时双向通信
- 💻 **现代化前端**：基于Quasar + Vue 3 + TypeScript
- 🐍 **Python后端**：FastAPI + Google Gemini API

## 系统架构

```
easy-prompt/
├── 后端服务 (Python FastAPI)
│   ├── main.py              # WebSocket服务端点
│   ├── conversation_handler.py  # 对话逻辑处理
│   ├── llm_helper.py        # LLM接口封装
│   ├── profile_manager.py   # 角色档案管理
│   └── evaluator_service.py # 评估服务
└── web-client/EasyP-webui/  # 前端应用 (Quasar)
    ├── src/
    │   ├── components/      # Vue组件
    │   ├── pages/          # 页面
    │   ├── services/       # WebSocket服务
    │   └── types/          # TypeScript类型定义
    └── ...
```

## 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **Google API Key**: 需要Gemini API访问权限

## 部署指南

**⚠️ 开始部署前请务必先阅读[环境变量配置](#环境变量配置)章节！**

### 1. Windows 部署

#### 1.1 准备工作

```cmd
# 克隆项目
git clone <repository-url>
cd easy-prompt

# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 升级pip
python -m pip install --upgrade pip
```

#### 1.2 安装Python依赖

```cmd
# 安装后端依赖
pip install -r requirements.txt
```

#### 1.3 配置环境变量

参考[环境变量配置](#环境变量配置)章节创建 `env/` 目录和配置文件。

#### 1.4 启动后端服务

```cmd
# 确保虚拟环境已激活
uvicorn main:app --reload
```

#### 1.5 安装和启动前端

```cmd
# 切换到前端目录
cd web-client\EasyP-webui

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 2. macOS/Linux 部署

#### 2.1 方式一：使用 Nix Flake（推荐）

如果你的系统安装了 Nix：

```bash
# 克隆项目
git clone <repository-url>
cd easy-prompt

# 使用Nix自动设置开发环境
nix develop

# 创建Python虚拟环境
python -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 配置环境变量（参考环境变量配置章节）
# 详细步骤请参考下方的"环境变量配置"章节

# 启动后端服务（开发模式，支持热重载）
uvicorn main:app --reload
```

在另一个终端中启动前端：

```bash
cd web-client/EasyP-webui
npm install
npm run dev
```

#### 2.2 方式二：传统方式（无Nix）

```bash
# 克隆项目
git clone <repository-url>
cd easy-prompt

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装Python依赖
pip install -r requirements.txt

# 配置环境变量（参考环境变量配置章节）
# 详细步骤请参考下方的"环境变量配置"章节

# 启动后端服务（开发模式，支持热重载）
uvicorn main:app --reload
```

在另一个终端中：

```bash
# 安装Node.js (如果未安装)
# Ubuntu/Debian: sudo apt install nodejs npm
# macOS: brew install node
# 或访问 https://nodejs.org/ 下载安装

# 切换到前端目录
cd web-client/EasyP-webui

# 安装前端依赖
npm install

# 启动开发服务器
npm run dev
```

## 环境变量配置

**⚠️ 重要：开始开发前必须正确配置环境变量**

在项目根目录下创建 `env/` 目录，并按照以下结构创建配置文件：

```
easy-prompt/
├── env/
│   ├── GOOGLE_API_KEY      # Google Gemini API密钥
│   ├── GEMINI_MODEL        # 对话模型名称
│   ├── EVALUATOR_MODEL     # 评估模型名称
│   └── SCORE_THRESHOLD     # 评估分数阈值
├── main.py
├── requirements.txt
└── ...
```

### 创建环境配置文件

**Windows:**

```cmd
mkdir env
echo your_google_api_key_here > env\GOOGLE_API_KEY
echo gemini-1.5-flash > env\GEMINI_MODEL
echo gemini-1.5-flash > env\EVALUATOR_MODEL
echo 80 > env\SCORE_THRESHOLD
```

**macOS/Linux:**

```bash
mkdir -p env
echo "your_google_api_key_here" > env/GOOGLE_API_KEY
echo "gemini-1.5-flash" > env/GEMINI_MODEL
echo "gemini-1.5-flash" > env/EVALUATOR_MODEL
echo "80" > env/SCORE_THRESHOLD
```

### 环境变量说明

| 文件名              | 说明                  | 示例值                | 备注                                   |
| ------------------- | --------------------- | --------------------- | -------------------------------------- |
| `GOOGLE_API_KEY`  | Google Gemini API密钥 | `your_api_key_here` | **必需**，从Google AI Studio获取 |
| `GEMINI_MODEL`    | 对话模型名称          | `gemini-1.5-flash`  | 用于生成对话内容                       |
| `EVALUATOR_MODEL` | 评估模型名称          | `gemini-1.5-flash`  | 用于评估角色档案                       |
| `SCORE_THRESHOLD` | 评估分数阈值          | `80`                | 决定何时可以生成最终提示词             |

**注意事项：**

- 每个文件只包含一行内容，无需引号
- `GOOGLE_API_KEY` 需要从 [Google AI Studio](https://aistudio.google.com/) 获取
- `env/` 目录已添加到 `.gitignore`，不会被提交到代码仓库
- 请妥善保管API密钥，不要泄露给他人

## 使用说明

1. **启动服务**：使用 `uvicorn main:app --reload` 启动后端服务（默认运行在 `http://127.0.0.1:8000`）
2. **访问前端**：打开浏览器访问 `http://localhost:9000`
3. **开始对话**：点击连接按钮，开始与AI对话构建角色
4. **查看评估**：右侧面板实时显示角色特征评估结果
5. **生成提示词**：当角色完整度足够时，确认生成最终提示词

## 开发说明

### 后端开发

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 启动开发服务器（支持热重载）
uvicorn main:app --reload
```

### 前端开发

```bash
cd web-client/EasyP-webui

# 开发模式（热重载）
npm run dev

# 构建生产版本
npm run build

# 类型检查
npm run type-check

# 代码格式化
npm run format
```

## 常见问题

### 1. 环境变量配置问题

**问题**：后端启动时提示找不到环境变量
```bash
# 检查env目录结构
ls -la env/  # Linux/macOS
dir env\     # Windows

# 确保文件存在且内容正确
cat env/GOOGLE_API_KEY  # Linux/macOS
type env\GOOGLE_API_KEY # Windows
```

**解决方案**：
- 确保 `env/` 目录在项目根目录下
- 检查所有必需的配置文件是否存在
- 确认文件内容格式正确（每个文件只有一行，无引号）

### 2. Python虚拟环境问题

**问题**：虚拟环境激活失败

```bash
# 删除虚拟环境重新创建
rm -rf venv  # Linux/macOS
# 或 rmdir /s venv  # Windows

# 重新创建
python -m venv venv
```

### 3. API密钥配置问题

**问题**：Google API访问失败

- 确保API密钥正确配置在 `env/GOOGLE_API_KEY` 文件中
- 检查API密钥是否有Gemini访问权限
- 确认API配额是否充足

### 4. 端口冲突问题

**问题**：端口8000或9000被占用

```bash
# 查看端口占用
netstat -an | grep 8000  # Linux/macOS
netstat -an | findstr 8000  # Windows

# 修改后端端口：编辑main.py中的port参数
# 修改前端端口：编辑web-client/EasyP-webui/quasar.config.ts
```

### 5. WebSocket连接问题

**问题**：前端无法连接后端

- 确保后端服务正常运行
- 检查防火墙设置
- 确认WebSocket URL配置正确（`ws://127.0.0.1:8000/ws/prompt`）

## 技术栈

- **后端**: Python, FastAPI, WebSocket, Google Gemini API
- **前端**: Vue 3, Quasar Framework, TypeScript, WebSocket
- **开发工具**: Nix Flake, ESLint, Prettier, vue-tsc

## 许可证

[添加你的许可证信息]

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

[添加你的联系方式]
