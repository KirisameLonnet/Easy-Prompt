# Easy-Prompt WebSocket API Documentation (v1.0)

This document provides detailed information about the WebSocket API for the Easy-Prompt service, designed for rich, interactive frontend clients.

## 1. Endpoint

The single WebSocket endpoint for all interactions is:

- **URL**: `ws://<your_server_address>:8000/ws/prompt`

By default, when running locally, this will be `ws://127.0.0.1:8000/ws/prompt`.

## 2. Message Format

All communication between the client and server is done via **JSON-formatted text messages**. Every message, in either direction, follows this structure:

```json
{
  "type": "message_type_string",
  "payload": {
    // ... message-specific data
  }
}
```

- `type`: A string that identifies the purpose of the message.
- `payload`: An object containing the data relevant to that message type.

---

## 3. Server-to-Client Messages

These are the message types the server can send to the client.

### `system_message`
Indicates a system-generated label or status, like "AI:".

- **Payload**: `{"message": "AI:"}`
- **When**: Sent right before the AI starts generating a response.

### `ai_response_chunk`
A piece of the AI's streaming response. The client should append these chunks to display the "typing" effect.

- **Payload**: `{"chunk": "Hello! I'm here to help you..."}`
- **When**: Sent repeatedly as the AI generates its conversational reply.

### `evaluation_update`
A status message indicating that the backend evaluator is analyzing the character profile.

- **Payload**: `{"message": "[评判员正在评估...]"}`
- **When**: Sent after the AI has finished its reply and the profile is being updated.

### `confirmation_request`
The AI has determined the character profile is complete and asks the user for confirmation to generate the final prompt.

- **Payload**: `{"reason": "The character profile seems complete enough. Shall I proceed?"}`
- **When**: Sent when the character score reaches the required threshold.

### `final_prompt_chunk`
A piece of the final, formatted Markdown prompt. The client should append these chunks to display the result.

- **Payload**: `{"chunk": "**【Role】**: Cyberpunk Hacker 'Nyx'\n"}`
- **When**: Sent repeatedly after the user confirms generation.

### `session_end`
Signals that the session has successfully concluded. The server will close the connection after this message.

- **Payload**: `{"message": "Application shutting down."}`
- **When**: Sent after the final prompt has been fully delivered.

### `error`
Indicates that an error occurred on the server.

- **Payload**: `{"message": "An unexpected error occurred."}`
- **When**: Sent if the server encounters an issue.

---

## 4. Client-to-Server Messages

These are the message types the client can send to the server.

### `user_response`
The user's reply in the conversation.

- **Payload**: `{"answer": "Her name is Nyx."}`
- **When**: Sent whenever the user provides input to the AI.

### `user_confirmation`
The user's response to a `confirmation_request`.

- **Payload**: `{"confirm": true}` or `{"confirm": false}`
- **When**: Sent after the user decides whether to generate the final prompt.

---

## 5. Interaction Example

Here is a typical message flow:

1.  **Client Connects**: Establishes a WebSocket connection.
2.  **Server -> Client**:
    ```json
    {"type": "system_message", "payload": {"message": "AI:"}}
    {"type": "ai_response_chunk", "payload": {"chunk": "Hello! "}}
    {"type": "ai_response_chunk", "payload": {"chunk": "What kind of character..."}}
    ```
3.  **Client -> Server**: User types and sends their initial idea.
    ```json
    {"type": "user_response", "payload": {"answer": "A cyberpunk hacker."}}
    ```
4.  **Server -> Client**: AI asks a follow-up question.
    ```json
    {"type": "system_message", "payload": {"message": "AI:"}}
    {"type": "ai_response_chunk", "payload": {"chunk": "Interesting! "}}
    {"type": "ai_response_chunk", "payload": {"chunk": "What's their alias?"}}
    {"type": "evaluation_update", "payload": {"message": "[评判员正在评估...]"}}
    ```
5.  ...The conversation continues for several turns...
6.  **Server -> Client**: The profile is ready, server asks for confirmation.
    ```json
    {"type": "confirmation_request", "payload": {"reason": "The profile is rich with detail. Ready to write the final prompt?"}}
    ```
7.  **Client -> Server**: User agrees.
    ```json
    {"type": "user_confirmation", "payload": {"confirm": true}}
    ```
8.  **Server -> Client**: Server streams the final prompt and ends the session.
    ```json
    {"type": "system_message", "payload": {"message": "AI:"}}
    {"type": "final_prompt_chunk", "payload": {"chunk": "**【Role】**..."}}
    {"type": "final_prompt_chunk", "payload": {"chunk": "\n**【Background】**..."}}
    // ...more chunks...
    {"type": "session_end", "payload": {"message": "Application shutting down."}}
    ```
9.  **Connection Closes**.
