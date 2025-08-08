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
        # The handler automatically prepares the initial greeting upon creation.
        handler = ConversationHandler()
        self.active_conversations[websocket] = handler
        
        # Send the pre-generated greeting to the client.
        await websocket.send_text(handler.initial_greeting)

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
            # The handler is already initialized, so we just handle the message.
            response = handler.handle_message(message)
            await websocket.send_text(response)