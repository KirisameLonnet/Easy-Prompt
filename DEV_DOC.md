# Easy-Prompt: The Intelligent RolePlay Prompt Generator (v5)

## 1. 项目简介

本项目是一个基于 Python 的**智能后端服务**，旨在通过与大语言模型（LLM）的**多轮对话**，帮助用户构建深度、立体、高质量的角色扮演（RolePlay）提示词。

其核心特性是**异步评估架构**：在用户与主对话LLM流畅交流的同时，一个独立的“评判员”LLM会在后台实时分析对话中产生的角色特点，并对其进行量化打分。这确保了对话的流畅性，并为用户提供了关于角色丰满度的即时反馈，最终在满足预设标准后，自动生成一份结构化的、高质量的Prompt。

项目同时支持 **WebSocket** (用于前端集成) 和 **CLI** (用于快速测试) 两种交互模式。

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
