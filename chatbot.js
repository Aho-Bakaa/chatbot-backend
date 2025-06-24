let QUESTION_BANK = [];
window.setUserExperience = setUserExperience;
document.addEventListener('DOMContentLoaded', () => {
  console.log('[Chatbot] DOM ready');
  window.chatbot = new GeminiChatbot();
  window.setUserExperience = setUserExperience;
  initVoiceFeature();
  loadQuestions();
});
async function loadQuestions() {
  try {
    const aimText = await fetch('aim.md').then(r => r.text());

    const res = await fetch('http://127.0.0.1:9100/extract_and_questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        aim_text: aimText,
        num_phrases: 5,
        num_questions_per_phrase: 2
      })
    });

    const data = await res.json();
    let questions = Array.isArray(data.questions) ? data.questions : [];

    // 2) Strictly sanitize + filter out anything containing "json" or backticks
    QUESTION_BANK = questions
      .map(q => String(q)
        .replace(/^[\s"'\[\]\{\}]+|[\s"'\[\]\{\},]+$/g, '')
        .trim()
      )
      .filter(q =>
        q &&                          // non-empty
        !q.toLowerCase().includes('json') &&
        !q.includes('```')
      );
  } catch (err) {
    console.error('Failed to load questions:', err);
  }
}
function setUserExperience(isExperienced) {
  const welcome    = document.getElementById('welcomeScreen');
  const expButtons = document.getElementById('experienceButtons');
  const dropdown   = document.getElementById('newUserDropdownContainer');
  const input      = document.getElementById('chatInput');
  const sendBtn    = document.getElementById('sendBtn');
  const newBtn = document.querySelector('.experience-btn');
document.addEventListener('DOMContentLoaded', () => {
  newBtn.disabled = true;
  newBtn.textContent = 'Loading questions…';
  loadQuestions().then(() => {
    newBtn.disabled = false;
    newBtn.textContent = "I'm new.";
  });
});

  // always enable the chat input now
  welcome.style.display = isExperienced ? 'none' : 'block';
  expButtons.style.display = isExperienced ? 'none' : 'none'; 
  input.disabled  = false;
  sendBtn.disabled = false;
  input.focus();

  if (!isExperienced) {
    // NEW user → show dropdown
    chatbot.addMessage('bot', "You're new! Please pick a question:");
    renderNewUserDropdown(dropdown);
  } else {
    // EXPERIENCED user → greet and let them type freely
    chatbot.addMessage('bot', "Welcome back! Ask me anything about this experiment.");
  }
}
function renderNewUserDropdown(container) {
  container.innerHTML = '';               // clear any old UI

  const select = document.createElement('select');
  select.id = 'newUserDropdown';

  // 1) Placeholder
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select a question…';
  placeholder.disabled = true;
  placeholder.selected = true;
  select.appendChild(placeholder);

  // 2) Add each cleaned question
  QUESTION_BANK.forEach((q, i) => {
    const opt = document.createElement('option');
    opt.value = q;         // use the text itself as value
    opt.textContent = q;   // ensures no raw JSON shows up
    select.appendChild(opt);
  });

  // 3) On pick, send via the same chat pipeline
  select.addEventListener('change', e => {
    const chosen = e.target.value;
    if (!chosen) return;
    sendUserMessage(chosen);
  });

  container.appendChild(select);
}
function initVoiceFeature() {
  const micBtn = document.getElementById('micBtn');
  let mediaRecorder, audioChunks = [];

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    micBtn.disabled = true;
    return;
  }

  micBtn.addEventListener('mousedown', async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    micBtn.classList.add('recording');

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  });

  micBtn.addEventListener('mouseup', () => {
    mediaRecorder.stop();
    micBtn.classList.remove('recording');
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      audioChunks = [];

      // send blob to server
      const form = new FormData();
      form.append('file', blob, 'speech.webm');
      const resp = await fetch('http://127.0.0.1:9100/speech_to_text', {
        method: 'POST',
        body: form
      });
      const { text } = await resp.json();
      document.getElementById('chatInput').value = text;
      sendUserMessage(text);
    };
  });
}
function sendUserMessage(text) {
  if (!text || !text.trim()) return;
  window.chatbot.addMessage('user', text);
  const input = document.getElementById('chatInput');
  input.value = '';
  document.getElementById('sendBtn').disabled = false;
  window.chatbot.sendMessage(text);
}

class GeminiChatbot {
  constructor() {
    this.apiUrl = 'http://127.0.0.1:9100/chat';
    this.history = [];
    this.typingElem = document.getElementById('typingIndicator');
    this.initElements();
    this.attachListeners();
  }
  initElements() {
    this.button = document.getElementById('chatButton');
    this.popup = document.getElementById('chatPopup');
    this.closeBtn = document.getElementById('closeBtn');
    this.refreshBtn = document.getElementById('refreshBtn');
    this.messages = document.getElementById('chatMessages');
    this.input = document.getElementById('chatInput');
    this.sendBtn = document.getElementById('sendBtn');
    this.welcome = document.getElementById('welcomeScreen');
    this.dropdownContainer = document.getElementById('newUserDropdownContainer');
    this.typingElem = document.getElementById('typingIndicator');
    if (!this.messages.contains(this.typingElem)) {
      this.messages.appendChild(this.typingElem);
    }
  }
  attachListeners() {
    this.button.addEventListener('click', () => this.toggleChat());
    this.closeBtn.addEventListener('click', () => this.toggleChat());
    this.refreshBtn.addEventListener('click', () => location.reload());
    this.sendBtn.addEventListener('click', () => sendUserMessage(this.input.value.trim()));
    this.input.addEventListener('keypress', e => { if (e.key === 'Enter') sendUserMessage(this.input.value.trim()); });
  }
  addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = content;
    if (this.messages.contains(this.typingElem)) this.messages.removeChild(this.typingElem);
    this.messages.appendChild(div);
    this.history.push({ role, content });
    this.scroll();
  }
  showTyping() { this.typingElem.style.display = 'block'; this.scroll(); }
  hideTyping() { this.typingElem.style.display = 'none';
   }
async sendMessage(text) {
  this.showTyping();
  try {
    const resp = await fetch(this.apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        has_used_before: true,
        conversation_history: this.history
      })
    });
    const json = await resp.json();

    this.hideTyping();
    if (json && json.response) {
      this.addMessage('bot', json.response);
    } else {
      this.addMessage('bot', '⚠️ No response received.');
    }
  } catch (e) {
    this.hideTyping();
    this.addMessage('bot', '❌ API error: ' + e.message);
  }
}
  toggleChat() {
    this.popup.style.display = this.popup.style.display === 'flex' ? 'none' : 'flex';
  }
  scroll() { this.messages.scrollTop = this.messages.scrollHeight; }
}

// ensure global chatbot variable
window.chatbot = window.chatbot || null;