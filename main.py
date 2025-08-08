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

@app.on_event("startup")
async def startup_event():
    """Load environment variables, initialize LLMs, and start background services."""
    env_dir = os.path.join(os.path.dirname(__file__), 'env')
    if os.path.exists(env_dir):
        for f in os.listdir(env_dir):
            with open(os.path.join(env_dir, f), 'r', encoding='utf-8') as file:
                os.environ[f] = file.read().strip()
    
    llm_helper.init_llm()
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

@app.websocket("/ws/prompt")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for interactive prompt generation."""
    await websocket.accept()
    
    handler = ConversationHandler()
    session_id = handler.profile_manager.session_id
    active_handlers[session_id] = handler
    
    try:
        # 1. Send initial greeting
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

        # 2. Main interaction loop
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            
            message_type = data.get("type")
            payload = data.get("payload", {})

            if message_type == "user_response":
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
