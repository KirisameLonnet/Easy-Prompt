import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from conversation_handler import ConversationHandler
from evaluator_service import EvaluatorService
from language_manager import lang_manager
import llm_helper
import os
from contextlib import asynccontextmanager

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
    description="Interactive prompt generation via WebSocket.",
    version="1.0.0",
    lifespan=lifespan,
)

evaluator_service = EvaluatorService()

# 移除全局的 API 配置，避免跨会话串扰
# In-memory storage for active handlers
active_handlers = {}

async def send_json(websocket: WebSocket, message_type: str, payload: dict):
    """Utility to send a structured JSON message."""
    await websocket.send_text(json.dumps({"type": message_type, "payload": payload}))


# 环境驱动的默认 API 配置探测
def _str2bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def get_default_api_config() -> dict:
    """Detect default API configuration from environment.
    优先使用 OpenAI 兼容模式（如 DeepSeek），否则退回 Gemini；若均未配置，则返回空配置。
    支持的变量：
      - OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS, NSFW_MODE
      - GOOGLE_API_KEY, GEMINI_MODEL, EVALUATOR_MODEL
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GOOGLE_API_KEY")
    nsfw_env = os.getenv("NSFW_MODE")
    nsfw_mode = _str2bool(nsfw_env, False)

    if openai_key:
        return {
            "api_type": "openai",
            "api_key": openai_key,
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1").rstrip('/'),
            "model": os.getenv("OPENAI_MODEL", "deepseek-chat"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
            "nsfw_mode": nsfw_mode,
        }

    if gemini_key:
        return {
            "api_type": "gemini",
            "api_key": gemini_key,
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            "evaluator_model": os.getenv("EVALUATOR_MODEL", ""),
            "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "4000")),
            "nsfw_mode": nsfw_mode,
        }

    # 未配置任一提供商，返回默认 OpenAI 空配置
    return {"api_type": "openai", "nsfw_mode": nsfw_mode}


def initialize_api(api_config: dict) -> bool:
    """Initialize API based on configuration"""
    try:
        nsfw_mode = api_config.get("nsfw_mode", False)
        if api_config.get("api_type") == "openai":
            # 允许从环境变量补齐缺失字段
            api_key = api_config.get("api_key") or os.getenv("OPENAI_API_KEY")
            base_url = api_config.get("base_url") or os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
            model = api_config.get("model") or os.getenv("OPENAI_MODEL", "deepseek-chat")
            temperature = api_config.get("temperature", float(os.getenv("OPENAI_TEMPERATURE", "0.7")))
            max_tokens = api_config.get("max_tokens", int(os.getenv("OPENAI_MAX_TOKENS", "4000")))

            if not api_key:
                print("错误: OpenAI API配置缺少参数: api_key")
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
            # 允许从环境变量补齐缺失字段
            api_key = api_config.get("api_key") or os.getenv("GOOGLE_API_KEY")
            model = api_config.get("model") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            evaluator_model = api_config.get("evaluator_model") or os.getenv("EVALUATOR_MODEL", "")
            temperature = api_config.get("temperature", float(os.getenv("GEMINI_TEMPERATURE", "0.7")))

            if not api_key:
                print("错误: Gemini API配置缺少参数: api_key")
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
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for interactive prompt generation."""
    await websocket.accept()

    handler = None
    session_id = None
    api_initialized = False
    # 将 API 配置限定为当前连接会话的本地变量，避免跨连接污染
    # 默认根据环境自动选择（优先 OpenAI 兼容）
    current_api_config = get_default_api_config()

    try:
        # 1. 等待 API 配置（若客户端提供），否则使用环境默认配置启动
        while not api_initialized:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            message_type = data.get("type")
            payload = data.get("payload", {})

            if message_type == "api_config":
                # Client is configuring API for THIS websocket only
                current_api_config.update(payload)

                # Initialize API with new configuration
                if initialize_api(current_api_config):
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
                # 使用环境默认配置启动（优先 OpenAI）
                if initialize_api(current_api_config):
                    api_initialized = True
                else:
                    await send_json(websocket, "error", {"message": "默认API初始化失败，请在设置中配置API"})
                    # 继续等待客户端发送 api_config

        # 2. Create conversation handler after API is initialized
        handler = ConversationHandler()
        session_id = handler.profile_manager.session_id
        active_handlers[session_id] = handler

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
                            is_ready = evaluation_result.get("is_ready_for_writing", False)

                            # 发送评估结果
                            await send_json(websocket, "evaluation_update", {
                                "message": f"[评估完成] {critique}",
                                "extracted_traits": extracted_traits,
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
                    handler = ConversationHandler()
                    session_id = handler.profile_manager.session_id
                    active_handlers[session_id] = handler
                else:
                    await send_json(websocket, "api_config_result", {
                        "success": False,
                        "message": "API重新配置失败"
                    })

            elif message_type == "user_response":
                await send_json(websocket, "system_message", {"message": lang_manager.t("YOU_PROMPT")})
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
                                    is_ready = evaluation_result.get("is_ready_for_writing", False)

                                    # 发送评估结果
                                    await send_json(websocket, "evaluation_update", {
                                        "message": f"[评估完成] {critique}",
                                        "extracted_traits": extracted_traits,
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
        active_handlers.pop(session_id, None)
        print(f"Cleaned up session: {session_id}")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Easy-Prompt API. Connect via WebSocket at /ws/prompt"}


@app.get("/api/status")
async def get_api_status():
    """Get generic API configuration status (no per-session state)."""
    from openai_helper import get_openai_config, is_openai_configured
    from gemini_helper import get_gemini_config, is_gemini_configured

    openai_env = bool(os.getenv("OPENAI_API_KEY"))
    gemini_env = bool(os.getenv("GOOGLE_API_KEY"))
    default_cfg = get_default_api_config()
    
    can_auto_start = False
    if default_cfg.get("api_type") == "openai" and (default_cfg.get("api_key") or is_openai_configured() or openai_env):
        can_auto_start = True
    if default_cfg.get("api_type") == "gemini" and (default_cfg.get("api_key") or is_gemini_configured() or gemini_env):
        can_auto_start = True

    status = {
        "supports": ["gemini", "openai"],
        "gemini_configured": bool(is_gemini_configured() or gemini_env),
        "openai_configured": bool(is_openai_configured() or openai_env),
        "gemini_config": {},
        "openai_config": {},
        "default_api_type": default_cfg.get("api_type"),
        "can_start_without_client_config": can_auto_start,
    }

    if status["gemini_configured"]:
        status["gemini_config"] = get_gemini_config()
    
    if status["openai_configured"]:
        status["openai_config"] = get_openai_config()

    return status
