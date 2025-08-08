import asyncio
import websockets
import json
import time

async def run_test():
    """
    Connects to the WebSocket server and runs a more realistic, multi-turn
    interaction test that won't hang.
    """
    uri = "ws://127.0.0.1:8000/ws/prompt"
    
    # A predefined script for our test user to follow
    dialogue = [
        "我想扮演一个在末日废土中挣扎求生的医生。",
        "她叫伊芙琳，性格坚韧但内心疲惫，见证了太多死亡，所以有点愤世嫉俗。",
        "她最大的秘密是，她曾经为了节省稀缺的药品，放弃了一个她认为无法救活的病人，这件事一直在折磨她。",
        "她使用一把老旧的手枪来自卫，但枪法很烂。她更擅长用手术刀，无论是救人还是...威慑敌人。"
    ]
    
    print(f"--- Connecting to {uri} ---")

    try:
        async with websockets.connect(uri) as websocket:
            print("--- Connection established. ---")

            # Function to receive a full response stream from the server
            async def receive_full_response():
                while True:
                    message_raw = await websocket.recv()
                    message = json.loads(message_raw)
                    msg_type = message.get("type")
                    print(f"S -> C: {message}")
                    # The conversation part is over when we get an evaluation update
                    # or a confirmation request.
                    if msg_type in ["evaluation_update", "confirmation_request"]:
                        return message # Return the last message for inspection

            # 1. Receive the initial greeting
            print("\n--- 1. Receiving initial greeting... ---")
            await receive_full_response()

            # 2. Go through the scripted dialogue
            for i, user_line in enumerate(dialogue):
                print(f"\n--- {i+2}. Sending user response: '{user_line}' ---")
                user_message = {
                    "type": "user_response",
                    "payload": {"answer": user_line}
                }
                await websocket.send(json.dumps(user_message))
                
                print("--- Receiving AI response... ---")
                last_message = await receive_full_response()

                # If server asks for confirmation, we can proceed
                if last_message.get("type") == "confirmation_request":
                    print("--- AI is ready to generate. Breaking dialogue loop. ---")
                    break
            
            # 3. Send the final confirmation
            confirmation_message = {
                "type": "user_confirmation",
                "payload": {"confirm": True}
            }
            print(f"\n--- Sending final confirmation... ---")
            await websocket.send(json.dumps(confirmation_message))

            # 4. Receive the final prompt
            print("\n--- Receiving final prompt... ---")
            while True:
                message_raw = await websocket.recv()
                message = json.loads(message_raw)
                msg_type = message.get("type")
                
                print(f"S -> C: {message}")

                if msg_type == "session_end":
                    print("--- Session ended successfully. Test complete. ---")
                    break

    except websockets.exceptions.ConnectionClosed as e:
        print(f"--- Connection closed: {e} ---")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Make sure you have the 'websockets' library installed:
    # pip install websockets
    asyncio.run(run_test())