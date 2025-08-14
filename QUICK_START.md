# 🚀 Easy Prompt - 快速开始指南

## 📋 5分钟快速启动

### 第一步：克隆项目
```bash
git clone https://github.com/KirisameLonnet/Easy-Prompt.git
cd easy-prompt
```

### 第二步：配置Python环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (macOS/Linux)
source venv/bin/activate
# Windows用户使用: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 第三步：启动后端服务
```bash
# 启动WebSocket服务器
python main.py
```
看到 `Uvicorn running on http://0.0.0.0:8000` 说明后端启动成功！

### 第四步：启动前端界面
```bash
# 新开一个终端，进入前端目录
cd web-client/EasyP-webui

# 安装前端依赖
npm install

# 启动开发服务器
npm run dev
```
看到 `Local: http://localhost:9000` 说明前端启动成功！

### 第五步：开始使用
1. 打开浏览器访问 `http://localhost:9000`
2. 点击右上角的"设置"按钮配置API
3. 推荐使用DeepSeek API（便宜好用）：
   - API类型：选择 "OpenAI兼容"
   - API密钥：在 [DeepSeek官网](https://platform.deepseek.com/) 获取
   - 其他选项保持默认即可
4. 点击"应用配置"，开始创建角色！

## 🔑 API配置指南

### DeepSeek (推荐)
- **优势**：价格便宜，中文理解好
- **获取API密钥**：访问 [DeepSeek Platform](https://platform.deepseek.com/)
- **配置**：
  - API类型：OpenAI兼容
  - Base URL：`https://api.deepseek.com/v1`
  - 模型：`deepseek-chat`

### OpenAI
- **优势**：功能强大，生态完善
- **获取API密钥**：访问 [OpenAI Platform](https://platform.openai.com/)
- **配置**：
  - API类型：OpenAI兼容
  - Base URL：`https://api.openai.com/v1`
  - 模型：`gpt-3.5-turbo` 或 `gpt-4`

### Google Gemini
- **优势**：免费额度大
- **获取API密钥**：访问 [Google AI Studio](https://makersuite.google.com/)
- **配置**：
  - API类型：Gemini
  - 模型：`gemini-2.5-flash`

## 🎯 使用技巧

### 角色创建建议
1. **从基础开始**：先描述角色的基本身份和背景
2. **逐步深入**：然后添加性格特征、爱好、经历等
3. **具体化**：避免太抽象，多用具体的例子和细节
4. **互动性**：描述角色如何与他人互动

### 常见问题
**Q：为什么AI一直在问问题，不生成最终提示词？**
A：系统会根据角色丰富度自动判断。当评分达到8分以上时会自动生成最终提示词。

**Q：如何查看当前的评估分数？**
A：界面右侧会显示实时的角色完善度评分和建议。

**Q：可以中途切换API吗？**
A：可以！随时点击设置按钮重新配置API。

**Q：生成的角色档案保存在哪里？**
A：保存在项目的 `sessions/` 目录下，每个会话都有独立的文件夹。

## 🛠️ 故障排除

### 常见错误及解决方案

#### 后端启动失败
```
Error: [Errno 48] Address already in use
```
**解决**：端口8000被占用，关闭占用的程序或修改端口：
```bash
python main.py --port 8001
```

#### 前端连接失败
```
WebSocket connection failed
```
**解决**：
1. 确认后端服务正在运行
2. 检查防火墙设置
3. 尝试刷新浏览器页面

#### API配置错误
```
API请求失败: 401 Unauthorized
```
**解决**：
1. 检查API密钥是否正确
2. 确认API账户有足够余额
3. 验证Base URL是否正确

#### 包安装失败
```
ERROR: Could not find a version that satisfies the requirement
```
**解决**：
1. 确认Python版本是3.8+
2. 升级pip：`pip install --upgrade pip`
3. 使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

## 📚 更多资源

- [完整开发文档](DEV_DOC.md) - 深入了解技术架构
- [WebSocket API文档](WEBSOCKET_API.md) - API接口说明
- [项目主页](README.md) - 项目详细介绍

## 💡 下一步

现在你已经成功运行了Easy Prompt！建议你：

1. 🎭 **创建第一个角色** - 跟着AI的引导，创建一个有趣的角色
2. 📖 **阅读生成的提示词** - 看看AI是如何组织角色信息的
3. 🔧 **探索不同的API** - 尝试不同的AI模型，比较效果
4. 🌟 **分享你的体验** - 在GitHub上给我们star并分享使用心得

Happy prompting! 🚀
