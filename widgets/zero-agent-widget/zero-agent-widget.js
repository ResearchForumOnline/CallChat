(function () {
  if (window.callchatZeroAgentLoaded) return;
  window.callchatZeroAgentLoaded = true;

  const config = Object.assign({
    endpoint: '/api/zero-agent',
    brand: 'CallChat Zero',
    prompt: 'Ask about setup, Element, Matrix, OpenZero, calls, or Shield.',
    maxChars: 900
  }, window.CallChatZeroAgent || {});

  const root = document.createElement('section');
  root.className = 'callchat-zero-agent-widget';
  root.setAttribute('data-open', 'false');
  root.innerHTML = `
    <div class="callchat-zero-agent-panel" role="dialog" aria-label="${escapeHtml(config.brand)} assistant">
      <div class="callchat-zero-agent-head">
        <div><strong>${escapeHtml(config.brand)}</strong><span>${escapeHtml(config.prompt)}</span></div>
        <button type="button" data-close aria-label="Close">x</button>
      </div>
      <div class="callchat-zero-agent-log" aria-live="polite"></div>
      <form class="callchat-zero-agent-form">
        <input name="message" maxlength="${Number(config.maxChars)}" autocomplete="off" placeholder="Ask CallChat..." />
        <button type="submit">Send</button>
      </form>
    </div>
    <button type="button" class="callchat-zero-agent-launcher" aria-label="Open CallChat assistant">Z</button>
  `;

  document.body.appendChild(root);
  const launcher = root.querySelector('.callchat-zero-agent-launcher');
  const close = root.querySelector('[data-close]');
  const form = root.querySelector('form');
  const input = root.querySelector('input');
  const log = root.querySelector('.callchat-zero-agent-log');

  launcher.addEventListener('click', () => root.setAttribute('data-open', root.getAttribute('data-open') !== 'true'));
  close.addEventListener('click', () => root.setAttribute('data-open', 'false'));

  addMessage('agent', 'Hello. I can help you set up CallChat, Matrix/Synapse, Element, OpenZero, calls, and safe Shield boundaries.');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = '';
    addMessage('user', message);
    const thinking = addMessage('agent', 'Checking...');
    try {
      const response = await fetch(config.endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message, source: location.hostname})
      });
      if (!response.ok) throw new Error('Agent endpoint unavailable');
      const data = await response.json();
      thinking.textContent = data.reply || data.message || 'I could not produce a reply.';
    } catch (error) {
      thinking.textContent = 'The local agent endpoint is not connected yet. Install OpenZero or point this widget at an approved backend.';
    }
  });

  function addMessage(kind, text) {
    const item = document.createElement('div');
    item.className = `callchat-zero-agent-msg ${kind === 'user' ? 'user' : 'agent'}`;
    item.textContent = text;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
    return item;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[char]));
  }
})();
