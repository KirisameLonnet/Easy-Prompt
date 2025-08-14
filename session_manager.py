from fastapi import WebSocket
from conversation_handler import ConversationHandler
from typing import Dict

class SessionManager:
    """
    Manages active WebSocket connections and their associated conversation handlers.
    """
    def __init__(self):
        self.active_conversations: Dict[WebSocket, ConversationHandler] = {}

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection, creates a ConversationHandler for it,
        and immediately sends the initial greeting message.
        """
        await websocket.accept()
        
        # Create a new handler for this session.
        handler = ConversationHandler()
        self.active_conversations[websocket] = handler
        
        # Get the initial greeting generator and send each chunk
        initial_greeting_stream = handler.get_initial_greeting()
        for chunk in initial_greeting_stream:
            await websocket.send_text(chunk)

    def disconnect(self, websocket: WebSocket):
        """
        Removes a disconnected WebSocket and its handler.
        """
        self.active_conversations.pop(websocket, None)

    async def handle_ws_message(self, websocket: WebSocket, message: str):
        """
        Handles a subsequent message from a WebSocket client by passing it
        to the appropriate ConversationHandler and sending back the response.
        """
        handler = self.active_conversations.get(websocket)
        if handler:
            # Get the response generator and send each chunk
            response_stream = handler.handle_message(message)
            for chunk in response_stream:
                await websocket.send_text(chunk)