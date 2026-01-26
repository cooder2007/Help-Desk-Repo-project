import { api } from './api.js';
import { getAuth } from './auth.js';

export function initChatbot() {
  const box = document.createElement('div');
  box.className = 'card';
  box.innerHTML = `
    <h3>🤖 Help Desk Bot</h3>
    <div id="chatLog" style="height:200px; overflow:auto; border:1px solid #1f2937; padding:8px;"></div>
    <input id="chatInput" placeholder="Ask me something..." />
  `;
  document.body.appendChild(box);

  const log = box.querySelector('#chatLog');
  const input = box.querySelector('#chatInput');

  input.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter' && input.value.trim()) {
      const msg = input.value;
      input.value = '';
      log.innerHTML += `<div><strong>You:</strong> ${msg}</div>`;

      const { token } = getAuth();
      const res = await api('/chatbot', {
        method: 'POST',
        token,
        body: { message: msg }
      });

      log.innerHTML += `<div><strong>Bot:</strong> ${res.reply}</div>`;
      log.scrollTop = log.scrollHeight;
    }
  });
}
