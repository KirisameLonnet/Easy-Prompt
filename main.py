import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from conversation_handler import ConversationHandler
from evaluator_service import EvaluatorService
from language_manager import lang_manager
import llm_helper
import os

# --- Application Setup ---
app = FastAPI(
    title="Easy-Prompt API",
    description="Interactive prompt generation via WebSocket.",
    version="1.0.0"
)
evaluator_service = EvaluatorService()

# Global API configuration
current_api_config = {
    "api_type": "openai",  # 默认使用OpenAI格式
    "api_key": None,
    "base_url": "https://api.deepseek.com/v1",  # 默认使用DeepSeek
    "model": "deepseek-chat",  # 默认使用DeepSeek Chat模型
    "temperature": 0.7,
    "max_tokens": 4000,
    "nsfw_mode": False  # 默认关闭R18内容
}

@app.on_event("startup")
async def startup_event():
    """Load environment variables and start background services."""
    env_dir = os.path.join(os.path.dirname(__file__), 'env')
    if os.path.exists(env_dir):
        for f in os.listdir(env_dir):
            with open(os.path.join(env_dir, f), 'r', encoding='utf-8') as file:
                os.environ[f] = file.read().strip()
    
    # Don't initialize LLM here - wait for client configuration
    # llm_helper.init_llm()
    evaluator_service.start()

@app.on_event("shutdown")
def shutdown_event():
    """Stop background services."""
    evaluator_service.stop()

# In-memory storage for active handlers
active_handlers = {}

async def send_json(websocket: WebSocket, message_type: str, payload: dict):
    """Utility to send a structured JSON message."""
    await websocket.send_text(json.dumps({"type": message_type, "payload": payload}))

def initialize_api(api_config: dict) -> bool:
    """Initialize API based on configuration"""
    try:
        nsfw_mode = api_config.get("nsfw_mode", False)
        if api_config["api_type"] == "openai":
            return llm_helper.init_llm(
                nsfw_mode=nsfw_mode,
                api_type="openai",
                api_key=api_config["api_key"],
                base_url=api_config["base_url"],
                model=api_config["model"],
                temperature=api_config.get("temperature", 0.7),
                max_tokens=api_config.get("max_tokens", 4000)
            )
        else:
            return llm_helper.init_llm(nsfw_mode=nsfw_mode, api_type="gemini")
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
    
    try:
        # 1. Wait for API configuration (if using OpenAI) or start with Gemini
        while not api_initialized:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            
            message_type = data.get("type")
            payload = data.get("payload", {})
            
            if message_type == "api_config":
                # Client is configuring API
                global current_api_config
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
                # Start with default Gemini configuration
                if initialize_api(current_api_config):
                    api_initialized = True
                else:
                    await send_json(websocket, "error", {"message": "默认API初始化失败"})
                    return
        
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
                # Allow runtime API reconfiguration
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
                    break # End session
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
            pass # Ignore errors if the socket is already closed
    finally:
        active_handlers.pop(session_id, None)
        print(f"Cleaned up session: {session_id}")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Easy-Prompt API. Connect via WebSocket at /ws/prompt"}

@app.get("/api/status")
async def get_api_status():
    """Get current API configuration status"""
    from openai_helper import get_openai_config
    
    status = {
        "current_api_type": current_api_config["api_type"],
        "gemini_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "openai_configured": False,
        "openai_config": {}
    }
    
    if current_api_config["api_type"] == "openai":
        from openai_helper import is_openai_configured
        status["openai_configured"] = is_openai_configured()
        status["openai_config"] = get_openai_config()
    
    return status
