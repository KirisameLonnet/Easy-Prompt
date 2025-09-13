import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from conversation_handler import ConversationHandler
from profile_manager import ProfileManager
from evaluator_service import EvaluatorService
from language_manager import lang_manager
import llm_helper
import os
from contextlib import asynccontextmanager
from threading import Lock

# 导入新的session管理模块
from schemas import (
    WebSocketMessage, UserResponse, UserConfirmation, ApiConfig, 
    ApiConfigResult, EvaluationUpdate, ChatMessage, MessageType
)
from session_service import SessionService, get_session_service
from session_routes import router as session_router

# 导入认证模块
from auth_routes import router as auth_router
from user_config_routes import router as user_config_router
from jwt_auth import get_current_active_user
from user_database import get_user_database

# 导入Supabase认证模块
from supabase_routes import router as supabase_router
from supabase_auth import get_current_user as get_supabase_user

# 添加API配置锁，确保多用户API配置不冲突
api_config_lock = Lock()

# --- Application Setup ---
# 使用 lifespan 替代已弃用的 on_event 钩子
@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle."""
    env_dir = os.path.join(os.path.dirname(__file__), 'env')
    if os.path.exists(env_dir):
        for f in os.listdir(env_dir):
            with open(os.path.join(env_dir, f), 'r', encoding='utf-8') as file:
                os.environ[f] = file.read().strip()
    
    evaluator_service.start()
    try:
        yield
    finally:
        evaluator_service.stop()

app = FastAPI(
    title="Easy-Prompt API",
    description="Interactive prompt generation via WebSocket and REST API.",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000", 
        "http://127.0.0.1:9000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 注册session管理路由
# 注册路由
app.include_router(session_router)
app.include_router(auth_router)
app.include_router(user_config_router)
app.include_router(supabase_router)  # 新增Supabase路由

evaluator_service = EvaluatorService()

async def send_json(websocket: WebSocket, message_type: str, payload: dict):
    """Utility to send a structured JSON message."""
    await websocket.send_text(json.dumps({"type": message_type, "payload": payload}))


# 环境驱动的默认 API 配置探测
def _str2bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def get_empty_api_config() -> dict:
    """返回空的API配置，要求用户必须手动配置"""
    return {
        "api_type": "openai",
        "api_key": "",
        "base_url": "",
        "model": "",
        "evaluator_model": "",
        "temperature": 0.7,
        "max_tokens": 4000,
        "nsfw_mode": False
    }


def initialize_api(api_config: dict) -> bool:
    """Initialize API based on configuration with thread safety"""
    with api_config_lock:  # 确保API配置的线程安全
        try:
            nsfw_mode = api_config.get("nsfw_mode", False)
            if api_config.get("api_type") == "openai":
                api_key = api_config.get("api_key", "")
                base_url = api_config.get("base_url", "")
                model = api_config.get("model", "")
                temperature = api_config.get("temperature", 0.7)
                max_tokens = api_config.get("max_tokens", 4000)

                if not api_key or not base_url or not model:
                    print("错误: OpenAI API配置不完整，缺少必要参数")
                    return False

                return llm_helper.init_llm(
                    nsfw_mode=nsfw_mode,
                    api_type="openai",
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            elif api_config.get("api_type") == "gemini":
                api_key = api_config.get("api_key", "")
                model = api_config.get("model", "")
                evaluator_model = api_config.get("evaluator_model", "")
                temperature = api_config.get("temperature", 0.7)

                if not api_key or not model:
                    print("错误: Gemini API配置不完整，缺少必要参数")
                    return False

                return llm_helper.init_llm(
                    nsfw_mode=nsfw_mode,
                    api_type="gemini",
                    api_key=api_key,
                    model=model,
                    evaluator_model=evaluator_model if evaluator_model else None,
                    temperature=temperature,
                )
            else:
                print(f"不支持的API类型: {api_config.get('api_type')}")
                return False
        except Exception as e:
            print(f"API初始化失败: {e}")
            return False


@app.websocket("/ws/prompt")
async def websocket_endpoint(
    websocket: WebSocket,
    session_service: SessionService = Depends(get_session_service)
):
    """Handles WebSocket connections for interactive prompt generation."""
    await websocket.accept()

    handler = None
    session_id = None
    api_initialized = False
    current_user = None
    # 将 API 配置限定为当前连接会话的本地变量，避免跨连接污染
    current_api_config = get_empty_api_config()

    try:
        # 1. 等待用户认证和API配置
        while not api_initialized:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            message_type = data.get("type")
            payload = data.get("payload", {})

            if message_type == "auth":
                # 用户认证
                token = payload.get("token")
                if not token:
                    await send_json(websocket, "auth_result", {
                        "success": False,
                        "message": "缺少认证令牌"
                    })
                    continue
                
                # 验证令牌
                from jwt_auth import verify_token
                token_data = verify_token(token)
                if not token_data:
                    await send_json(websocket, "auth_result", {
                        "success": False,
                        "message": "认证令牌无效"
                    })
                    continue
                
                # 获取用户信息
                user_db = get_user_database()
                current_user = user_db.get_user_by_id(token_data.user_id)
                if not current_user:
                    await send_json(websocket, "auth_result", {
                        "success": False,
                        "message": "用户不存在"
                    })
                    continue
                
                await send_json(websocket, "auth_result", {
                    "success": True,
                    "message": f"认证成功，欢迎 {current_user.username}",
                    "user": {
                        "id": current_user.id,
                        "username": current_user.username,
                        "role": current_user.role
                    }
                })
                
                # 尝试加载用户的API配置
                user_api_config = user_db.get_user_api_config(current_user.id)
                if user_api_config:
                    current_api_config.update(user_api_config)
                    if initialize_api(current_api_config):
                        await send_json(websocket, "api_config_result", {
                            "success": True,
                            "message": f"已加载保存的API配置: {current_api_config['api_type']}"
                        })
                        api_initialized = True
                    else:
                        await send_json(websocket, "api_config_result", {
                            "success": False,
                            "message": "保存的API配置无效，请重新配置"
                        })

            elif message_type == "api_config":
                # 客户端配置API
                if not current_user:
                    await send_json(websocket, "error", {
                        "message": "请先进行用户认证"
                    })
                    continue
                
                current_api_config.update(payload)

                # Initialize API with new configuration
                if initialize_api(current_api_config):
                    # 保存用户的API配置
                    user_db = get_user_database()
                    user_db.save_api_config(current_user.id, current_api_config)
                    
                    await send_json(websocket, "api_config_result", {
                        "success": True,
                        "message": f"API已配置: {current_api_config['api_type']}"
                    })
                    api_initialized = True
                else:
                    await send_json(websocket, "api_config_result", {
                        "success": False,
                        "message": "API配置失败，请检查配置参数"
                    })

            elif message_type == "start_session":
                # 要求用户必须先认证和配置API
                if not current_user:
                    await send_json(websocket, "error", {
                        "message": "请先进行用户认证"
                    })
                else:
                    await send_json(websocket, "error", {
                        "message": "请先配置API，点击设置按钮进行配置"
                    })
                # 继续等待客户端发送认证或配置

        # 2. Create conversation handler after API is initialized
        # 尝试恢复现有session，如果没有则创建新的
        existing_session_id = ProfileManager.find_existing_session()
        if existing_session_id:
            print(f"恢复现有session: {existing_session_id}")
            session = await session_service.get_session(existing_session_id)
            if session:
                handler = session_service.get_handler(existing_session_id)
                if not handler:
                    handler = session_service.create_handler(existing_session_id)
                session_id = existing_session_id
            else:
                # 创建新session
                session = await session_service.create_session()
                handler = session_service.get_handler(session.id)
                session_id = session.id
        else:
            print("创建新session")
            session = await session_service.create_session()
            handler = session_service.get_handler(session.id)
            session_id = session.id

        # 3. Send initial greeting
        await send_json(websocket, "system_message", {"message": lang_manager.t("AI_PROMPT")})
        initial_stream = handler.get_initial_greeting()
        for chunk in initial_stream:
            if chunk.startswith("EVALUATION_TRIGGER::"):
                evaluation_message = chunk.split("::", 1)[1]
                await send_json(websocket, "evaluation_update", {"message": evaluation_message})

                # 执行实际的评估逻辑
                try:
                    full_profile = handler.profile_manager.get_full_profile()
                    if full_profile:
                        from llm_helper import evaluate_profile
                        evaluation_result = evaluate_profile(full_profile)
                        if evaluation_result:
                            critique = evaluation_result.get("critique", "")
                            extracted_traits = evaluation_result.get("extracted_traits", [])
                            extracted_keywords = evaluation_result.get("extracted_keywords", [])
                            evaluation_score = evaluation_result.get("evaluation_score")
                            completeness_breakdown = evaluation_result.get("completeness_breakdown", {})
                            suggestions = evaluation_result.get("suggestions", [])
                            is_ready = evaluation_result.get("is_ready_for_writing", False)

                            # 发送完整的评估结果
                            await send_json(websocket, "evaluation_update", {
                                "message": f"[评估完成] {critique}",
                                "extracted_traits": extracted_traits,
                                "extracted_keywords": extracted_keywords,
                                "evaluation_score": evaluation_score,
                                "completeness_breakdown": completeness_breakdown,
                                "suggestions": suggestions,
                                "is_ready": is_ready
                            })
                        else:
                            await send_json(websocket, "evaluation_update", {"message": "[评估服务] 评估失败"})
                    else:
                        await send_json(websocket, "evaluation_update", {"message": "[评估服务] 档案为空"})
                except Exception as e:
                    print(f"评估过程出错: {e}")
                    await send_json(websocket, "evaluation_update", {"message": f"[评估服务] 评估出错: {str(e)}"})

            else:
                await send_json(websocket, "ai_response_chunk", {"chunk": chunk})

        # 4. Main interaction loop
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            message_type = data.get("type")
            payload = data.get("payload", {})

            if message_type == "api_config":
                # Allow runtime API reconfiguration for THIS websocket only
                current_api_config.update(payload)
                if initialize_api(current_api_config):
                    await send_json(websocket, "api_config_result", {
                        "success": True,
                        "message": f"API已重新配置: {current_api_config['api_type']}"
                    })
                    # Reset handler with new API
                    handler = session_service.create_handler(session_id)
                else:
                    await send_json(websocket, "api_config_result", {
                        "success": False,
                        "message": "API重新配置失败"
                    })

            elif message_type == "user_response":
                await send_json(websocket, "system_message", {"message": lang_manager.t("YOU_PROMPT")})
                
                # 添加用户消息到session
                user_message = ChatMessage(
                    id=f"msg_{int(asyncio.get_event_loop().time() * 1000)}",
                    type=MessageType.USER,
                    content=payload.get("answer", ""),
                    is_complete=True
                )
                await session_service.add_message_to_session(session_id, user_message)
                
                response_generator = handler.handle_message(payload.get("answer", ""))

                for chunk in response_generator:
                    if chunk.startswith("CONFIRM_GENERATION::"):
                        reason = chunk.split("::", 1)[1]
                        await send_json(websocket, "confirmation_request", {"reason": reason})
                    elif chunk.startswith("EVALUATION_TRIGGER::"):
                        evaluation_message = chunk.split("::", 1)[1]
                        await send_json(websocket, "evaluation_update", {"message": evaluation_message})

                        # 执行实际的评估逻辑
                        try:
                            full_profile = handler.profile_manager.get_full_profile()
                            if full_profile:
                                from llm_helper import evaluate_profile
                                evaluation_result = evaluate_profile(full_profile)
                                if evaluation_result:
                                    critique = evaluation_result.get("critique", "")
                                    extracted_traits = evaluation_result.get("extracted_traits", [])
                                    extracted_keywords = evaluation_result.get("extracted_keywords", [])
                                    evaluation_score = evaluation_result.get("evaluation_score")
                                    completeness_breakdown = evaluation_result.get("completeness_breakdown", {})
                                    suggestions = evaluation_result.get("suggestions", [])
                                    is_ready = evaluation_result.get("is_ready_for_writing", False)

                                    # 发送完整的评估结果
                                    await send_json(websocket, "evaluation_update", {
                                        "message": f"[评估完成] {critique}",
                                        "extracted_traits": extracted_traits,
                                        "extracted_keywords": extracted_keywords,
                                        "evaluation_score": evaluation_score,
                                        "completeness_breakdown": completeness_breakdown,
                                        "suggestions": suggestions,
                                        "is_ready": is_ready
                                    })
                                else:
                                    await send_json(websocket, "evaluation_update", {"message": "[评估服务] 评估失败"})
                            else:
                                await send_json(websocket, "evaluation_update", {"message": "[评估服务] 档案为空"})
                        except Exception as e:
                            print(f"评估过程出错: {e}")
                            await send_json(websocket, "evaluation_update", {"message": f"[评估服务] 评估出错: {str(e)}"})

                    else:
                        await send_json(websocket, "ai_response_chunk", {"chunk": chunk})

            elif message_type == "user_confirmation":
                if payload.get("confirm", False):
                    await send_json(websocket, "system_message", {"message": lang_manager.t("AI_PROMPT")})
                    final_prompt_stream = handler.finalize_prompt()
                    for chunk in final_prompt_stream:
                        if chunk == "::FINAL_PROMPT_END::":
                            break
                        await send_json(websocket, "final_prompt_chunk", {"chunk": chunk})
                    await send_json(websocket, "session_end", {"message": lang_manager.t("APP_SHUTDOWN")})
                    break  # End session
                else:
                    await send_json(websocket, "system_message", {"message": lang_manager.t("YOU_PROMPT")})
                    await send_json(websocket, "ai_response_chunk", {"chunk": lang_manager.t('CONTINUE_PROMPT')})

    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        print(f"An error occurred in session {session_id}: {e}")
        try:
            await send_json(websocket, "error", {"message": str(e)})
        except:
            pass  # Ignore errors if the socket is already closed
    finally:
        if session_id:
            session_service.remove_handler(session_id)
            print(f"Cleaned up session: {session_id}")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Easy-Prompt API. Connect via WebSocket at /ws/prompt"}


@app.get("/api/status")
async def get_api_status():
    """Get API configuration status - 不再支持自动配置"""
    status = {
        "supports": ["gemini", "openai"],
        "requires_manual_config": True,
        "message": "请在前端配置API密钥和模型信息"
    }
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
