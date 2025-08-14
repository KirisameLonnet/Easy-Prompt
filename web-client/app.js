const chat = document.getElementById('chat');
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send');
const dialog = document.getElementById('floating-dialog');
const dialogMsg = document.getElementById('dialog-message');
const confirmBtn = document.getElementById('confirm-generate');
const ignoreBtn = document.getElementById('ignore-dialog');

const ws = new WebSocket(`ws://${location.host}/ws/prompt`);

function appendMessage(sender, message) {
    const div = document.createElement('div');
    div.textContent = `${sender}: ${message}`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const { type, payload } = data;

    switch (type) {
        case 'system_message':
            appendMessage('系统', payload.message);
            break;
        case 'ai_response_chunk':
            appendMessage('AI', payload.chunk);
            break;
        case 'evaluation_update':
            if (payload.message) {
                appendMessage('评估', payload.message);
            }
            break;
        case 'confirmation_request':
            dialogMsg.textContent = payload.reason || '档案已准备好，是否生成 Prompt?';
            dialog.style.display = 'block';
            break;
        case 'final_prompt_chunk':
            appendMessage('Prompt', payload.chunk);
            break;
        case 'session_end':
            appendMessage('系统', payload.message);
            ws.close();
            break;
    }
};

sendBtn.onclick = () => {
    const text = input.value.trim();
    if (!text) return;
    ws.send(JSON.stringify({ type: 'user_response', payload: { answer: text } }));
    appendMessage('你', text);
    input.value = '';
};

confirmBtn.onclick = () => {
    ws.send(JSON.stringify({ type: 'user_confirmation', payload: { confirm: true } }));
    dialog.style.display = 'none';
};

ignoreBtn.onclick = () => {
    ws.send(JSON.stringify({ type: 'user_confirmation', payload: { confirm: false } }));
    dialog.style.display = 'none';
};
