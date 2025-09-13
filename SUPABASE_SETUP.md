# Supabase 设置指南

## 1. 创建Supabase项目

1. 访问 [Supabase](https://supabase.com)
2. 注册/登录账户
3. 创建新项目
4. 选择组织并输入项目名称
5. 设置数据库密码
6. 选择区域（建议选择离用户最近的区域）

## 2. 获取项目配置

在项目仪表板中，找到以下信息：

- **Project URL**: `https://your-project.supabase.co`
- **anon public key**: 在 Settings > API 中找到
- **service_role key**: 在 Settings > API 中找到（用于服务端操作）

## 3. 设置环境变量

创建 `.env` 文件并添加：

```bash
# Supabase配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# 其他配置
EASYPROMPT_SECRET_KEY=your-secret-key-change-this-in-production
```

## 4. 运行数据库迁移

1. 在Supabase项目中，进入 SQL Editor
2. 复制 `supabase_migration.sql` 文件内容
3. 粘贴到SQL编辑器中
4. 点击 "Run" 执行迁移

这将创建以下表：
- `profiles` - 用户配置文件
- `api_configs` - 用户API配置（加密存储）
- `sessions` - 聊天会话

## 5. 配置认证设置

在Supabase项目中：

1. 进入 **Authentication > Settings**
2. 配置以下设置：
   - **Site URL**: `http://localhost:9000` (开发环境)
   - **Redirect URLs**: 添加 `http://localhost:9000/**`
   - **JWT expiry**: 设置为合适的值（默认1小时）

## 6. 启用邮箱认证

1. 进入 **Authentication > Providers**
2. 确保 **Email** 提供商已启用
3. 配置SMTP设置（可选，用于发送确认邮件）

## 7. 配置行级安全策略

迁移脚本已经自动创建了RLS策略，确保：
- 用户只能访问自己的数据
- API配置和会话数据按用户隔离

## 8. 测试设置

启动后端服务：

```bash
source .venv/bin/activate
export SUPABASE_URL="your-url"
export SUPABASE_ANON_KEY="your-key"
export SUPABASE_SERVICE_KEY="your-service-key"
export EASYPROMPT_SECRET_KEY="your-secret-key"
uvicorn main:app --reload
```

## 9. 前端配置

前端会自动使用新的Supabase认证服务。确保：

1. 后端运行在 `http://127.0.0.1:8000`
2. 前端运行在 `http://localhost:9000`
3. CORS配置正确

## 10. 功能特性

### 认证功能
- ✅ 用户注册（邮箱+密码）
- ✅ 用户登录
- ✅ 自动令牌刷新
- ✅ 密码重置
- ✅ 用户登出

### 数据安全
- ✅ API密钥加密存储
- ✅ 行级安全策略
- ✅ 用户数据隔离
- ✅ 自动数据清理

### 用户体验
- ✅ 自动用户配置文件创建
- ✅ 跨设备同步
- ✅ 实时数据更新
- ✅ 安全的会话管理

## 11. 故障排除

### 常见问题

1. **认证失败**
   - 检查环境变量是否正确设置
   - 确认Supabase项目URL和密钥正确

2. **数据库连接失败**
   - 检查网络连接
   - 确认Supabase项目状态正常

3. **RLS策略错误**
   - 检查用户是否已登录
   - 确认令牌是否有效

4. **API配置保存失败**
   - 检查加密密钥是否正确
   - 确认用户权限

### 调试模式

在开发环境中，可以启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 12. 生产环境部署

### 环境变量
- 使用强密钥
- 启用HTTPS
- 配置正确的CORS域名

### 数据库
- 定期备份
- 监控性能
- 设置适当的连接池

### 安全
- 定期轮换密钥
- 监控异常登录
- 启用审计日志
