/**
 * Aura Chat v3 — Main Application Logic
 * 
 * Core workflow:
 * 1. User pastes what partner said
 * 2. All 6 APIs fire in parallel
 * 3. User picks the best response or regenerates with feedback
 * 4. Selected response logs to chat as "sent"
 * 5. AI analyzes conversation metrics in background
 */

import { generateAllParallel, rewriteSuggestion, analyzeConversation, generateCoachReport, generatePartnerReply, API_REGISTRY } from './api.js';

// ==================== STATE ====================
const STORAGE_KEY = 'aura_chat_v3_state';

// Current icebreaker language + category tracking
let iceLang = 'en';
let iceCat = 'openers';

// Multilingual Icebreakers
const ICEBREAKERS = {
  en: {
    openers: [
      "You have the kind of vibe that makes a room feel smaller — in a good way.",
      "I feel like you're the type who laughs at your own jokes. Am I right?",
      "If I had to guess your love language, I'd say... quality time. Close?",
      "Your energy is contagious. What's your secret?",
      "I just got the weirdest urge to tell you something really random.",
      "I bet you're the person everyone goes to for advice, right?",
      "Something about your profile just made me stop scrolling."
    ],
    teasing: [
      "You really typed that and thought 'yeah this is it' huh?",
      "I was going to say something sweet, but I don't want to spoil you yet.",
      "Careful, you're starting to make me like you.",
      "You're cute when you try to be mysterious. Key word: try.",
      "I didn't expect you to be this interesting. Now I'm concerned.",
      "You're dangerously good at this. Should I be worried?",
      "Okay, now I KNOW you practiced that line. Admit it."
    ],
    deep: [
      "What's one thing you wish people understood about you without having to explain?",
      "If you could relive one moment from your life, which one would it be?",
      "Do you think we meet people by accident or for a reason?",
      "What's your biggest fear when it comes to relationships?",
      "If I could see one memory from your childhood, which one would you show me?",
      "What does a perfect day look like for you, start to finish?",
      "Is there something you've never told anyone that you'd tell a stranger?"
    ],
    saves: [
      "My bad, I got distracted by life. But I'm here now, and that's what matters 😌",
      "Okay, let me try again. Pretend that last message never happened.",
      "I think my brain just lagged. Give me a second to actually think.",
      "Alright, I'll be real — I have no smooth response to that. You win this round.",
      "I was trying to be cool but honestly I'm just a little awkward sometimes.",
      "You caught me off guard, that doesn't happen often.",
      "I'm gonna blame autocorrect for whatever I just said."
    ]
  },
  hi: {
    openers: [
      "तुम्हारे बारे में कुछ तो अलग है, पता नहीं क्या 🤔",
      "तुम्हारी वाइब बहुत अच्छी है, बताओ राज़ क्या है?",
      "मुझे लगता है तुम वो हो जिनसे सबसे पहले बात करने का मन करता है।",
      "अगर मैं तुम्हारी love language guess करूं तो... quality time?",
      "कुछ बातें बिना वजह शुरू होती हैं, ये भी वैसी ही है 😊",
      "तुमसे बात करके ऐसा लगता है जैसे पुरानी जान हो।",
      "बताओ, सबसे ज़्यादा खुश कब होती हो?"
    ],
    teasing: [
      "तुमने वो लिखा और सोचा 'हाँ ये सही है'? सच में? 😂",
      "मैं कुछ sweet बोलने वाला था, पर तुम्हें spoil नहीं करना चाहता अभी।",
      "सावधान, तुम मुझे पसंद आने लगी हो 😏",
      "तुम mysterious बनने की कोशिश करती हो तो cute लगती हो।",
      "मुझे expect नहीं था कि तुम इतनी interesting होगी।",
      "तुम इतना अच्छा reply देती हो, practice करी है क्या? 😄",
      "अभी तो सिर्फ शुरुआत है, रुको ज़रा 😎"
    ],
    deep: [
      "एक चीज़ बताओ जो तुम चाहती हो लोग बिना बताए समझ जाएं?",
      "अगर ज़िन्दगी का कोई एक पल दोबारा जी सको तो कौन सा?",
      "तुम्हें लगता है लोग इत्तेफाक से मिलते हैं या किसी वजह से?",
      "रिश्तों में तुम्हारा सबसे बड़ा डर क्या है?",
      "अगर मैं तुम्हारी एक बचपन की याद देख सकूं, तो कौन सी दिखाओगी?",
      "तुम्हारा perfect दिन कैसा होता है, शुरू से आखिर तक?",
      "कोई ऐसी बात जो किसी को नहीं बताई, पर एक अजनबी को बता दोगी?"
    ],
    saves: [
      "Sorry यार, ज़िन्दगी में उलझ गया था। पर अब यहाँ हूँ 😌",
      "चलो दोबारा try करते हैं, पिछला message भूल जाओ।",
      "मेरा दिमाग अभी lag कर गया, ek second दो।",
      "सच बताऊं? तुम्हारा reply सुनकर मेरे पास कोई smooth जवाब नहीं है।",
      "मैं cool बनने की कोशिश कर रहा था पर honestly थोड़ा awkward हूँ 😅",
      "Autocorrect को blame करो, मुझे नहीं 😂",
      "तुमने off guard पकड़ लिया, ये अक्सर नहीं होता।"
    ]
  },
  hing: {
    openers: [
      "Tumhare baare mein kuch toh alag hai, pata nahi kya 🤔",
      "Tumhari vibe bahut acchi hai, batao raaz kya hai?",
      "Mujhe lagta hai tum woh ho jinse sabse pehle baat karne ka mann karta hai.",
      "Agar main tumhari love language guess karun toh... quality time?",
      "Kuch baatein bina wajah shuru hoti hain, ye bhi waisi hi hai 😊",
      "Tumse baat karke aisa lagta hai jaise purani jaan ho.",
      "Batao, sabse zyada khush kab hoti ho?"
    ],
    teasing: [
      "Tumne woh likha aur socha 'haan ye sahi hai'? Seriously? 😂",
      "Main kuch sweet bolne wala tha, par tumhe spoil nahi karna chahta abhi.",
      "Savdhaan, tum mujhe pasand aane lagi ho 😏",
      "Tum mysterious banne ki koshish karti ho toh cute lagti ho.",
      "Mujhe expect nahi tha ki tum itni interesting hogi.",
      "Tum itna accha reply deti ho, practice kari hai kya? 😄",
      "Abhi toh sirf shuruat hai, ruko zara 😎"
    ],
    deep: [
      "Ek cheez batao jo tum chahti ho log bina bataye samajh jaayein?",
      "Agar zindagi ka koi ek pal dobara ji sako toh kaunsa?",
      "Tumhe lagta hai log ittefaq se milte hain ya kisi wajah se?",
      "Relationships mein tumhara sabse bada dar kya hai?",
      "Agar main tumhari ek bachpan ki yaad dekh sakun, toh kaunsi dikhaaogi?",
      "Tumhara perfect din kaisa hota hai, start se end tak?",
      "Koi aisi baat jo kisiko nahi batayi, par ek stranger ko bata dogi?"
    ],
    saves: [
      "Sorry yaar, zindagi mein ulajh gaya tha. Par ab yahan hun 😌",
      "Chalo dobara try karte hain, last message bhul jao.",
      "Mera dimaag abhi lag kar gaya, ek second do.",
      "Sach bataun? Tumhara reply sunke mere paas koi smooth jawab nahi hai.",
      "Main cool banne ki koshish kar raha tha par honestly thoda awkward hun 😅",
      "Autocorrect ko blame karo, mujhe nahi 😂",
      "Tumne off guard pakad liya, ye aksar nahi hota."
    ]
  }
};

let state = loadState();

function defaultState(boyName, girlName) {
  const gName = girlName || 'Chloe';
  const bName = boyName || 'You';
  return {
    sessions: [{
      id: 'default', name: gName, gender: 'girl',
      girlNature: 'Playful, witty, slightly sarcastic but sweet. She teases but always comes back with something cute.',
      boyNature: `Name: ${bName}. Confident, charming, good sense of humor. Knows when to be serious.`,
      mood: 'rizz', language: 'auto', notes: '',
      messages: [], attractionHistory: [70],
      sentLog: [],
      metrics: { psychology: 'neutral', psychologyText: 'Analyzing...', attraction: 70, rizzScore: 0, rizzRating: '', conversationHealth: 50, redFlags: [], moodSuggestion: '' },
      relStage: 'talking'
    }],
    activeId: 'default',
    soundOn: true,
    onboarded: true,
    boyName: bName,
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const s = JSON.parse(raw);
      // Ensure new fields exist on each session
      s.sessions.forEach(sess => {
        if (!sess.sentLog) sess.sentLog = [];
        if (!sess.metrics) sess.metrics = { psychology: 'neutral', psychologyText: 'Analyzing...', attraction: 70, rizzScore: 0, rizzRating: '', conversationHealth: 50, redFlags: [], moodSuggestion: '' };
        if (!sess.attractionHistory) sess.attractionHistory = [70];
      });
      return s;
    }
    // Try migrating v2 state
    const v2 = localStorage.getItem('aura_chat_v2_state');
    if (v2) {
      const old = JSON.parse(v2);
      // Migrate
      old.sessions.forEach(sess => {
        if (!sess.sentLog) sess.sentLog = [];
        if (!sess.metrics) sess.metrics = { psychology: 'neutral', psychologyText: 'Analyzing...', attraction: 70, rizzScore: 0, rizzRating: '', conversationHealth: 50, redFlags: [], moodSuggestion: '' };
        if (!sess.attractionHistory) sess.attractionHistory = [70];
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(old));
      return old;
    }
  } catch (e) { console.error('State load error:', e); }
  // Fresh user — show onboarding
  return { sessions: [], activeId: null, soundOn: true, onboarded: false, boyName: '' };
}

function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
function active() { return state.sessions.find(s => s.id === state.activeId) || state.sessions[0]; }

// ==================== AUDIO ====================
let audioCtx;
function playSound(type) {
  if (!state.soundOn) return;
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);
    if (type === 'send') { osc.frequency.value = 880; gain.gain.value = 0.08; }
    else if (type === 'receive') { osc.frequency.value = 660; gain.gain.value = 0.06; }
    else if (type === 'select') { osc.frequency.value = 1200; gain.gain.value = 0.05; }
    else { osc.frequency.value = 440; gain.gain.value = 0.04; }
    osc.start(); osc.stop(audioCtx.currentTime + 0.12);
  } catch (e) {}
}

// ==================== DOM REFS ====================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// Left
const sessionsList = $('#sessions-list');
const girlNatureEl = $('#girl-nature');
const boyNatureEl = $('#boy-nature');
const charNotesEl = $('#char-notes');
const langSelect = $('#lang-select');
const iceList = $('#ice-list');

// Center
const chatMsgsEl = $('#chat-msgs');
const emptyState = $('#empty-state');
const partnerNameEl = $('#partner-name');
const chatMoodLabel = $('#chat-mood-label');
const typingWrap = $('#typing-wrap');
const sandboxToggle = $('#sandbox-toggle');
const sandboxForm = $('#sandbox-form');
const sandboxInput = $('#sandbox-input');
const chatLabel = $('#chat-label');

// Right
const partnerMsgEl = $('#partner-msg');
const genBtn = $('#gen-btn');
const arenaCards = $('#arena-cards');
const arenaCounter = $('#arena-counter');
const feedbackInput = $('#feedback-input');
const regenBtn = $('#regen-btn');
const actualSentEl = $('#actual-sent');
const sentLogList = $('#sent-log-list');

// Metrics
const psychBadge = $('#psych-badge');
const psychText = $('#psych-text');
const attractionPct = $('#attraction-pct');
const attractionFill = $('#attraction-fill');
const healthPct = $('#health-pct');
const healthFill = $('#health-fill');
const relStage = $('#rel-stage');
const redFlagsArea = $('#red-flags-area');
const redFlagsList = $('#red-flags-list');
const attractSvg = $('#attract-svg');

// ==================== RENDER ====================
function renderAll() {
  renderSessions();
  renderPrompts();
  renderChat();
  renderMetrics();
  renderSentLog();
  renderGraph();
  renderIcebreakers(iceCat, iceLang);
  updateMoodPills();
  lucide.createIcons();
}

function renderSessions() {
  const sess = active();
  sessionsList.innerHTML = state.sessions.map(s => `
    <div class="sess ${s.id === state.activeId ? 'active' : ''}" data-id="${s.id}">
      <img class="sess-avatar" src="https://ui-avatars.com/api/?name=${encodeURIComponent(s.name)}&background=${s.id === state.activeId ? '7c3aed' : '1e293b'}&color=fff&size=64&bold=true" alt="${s.name}">
      <div class="sess-info">
        <span class="sess-name">${s.name}</span>
        <span class="sess-stage">${s.relStage || 'talking'}</span>
      </div>
      ${state.sessions.length > 1 ? `<button class="icon-btn sess-del" data-del="${s.id}" title="Delete"><i data-lucide="x"></i></button>` : ''}
    </div>
  `).join('');

  // Events
  sessionsList.querySelectorAll('.sess').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target.closest('.sess-del')) return;
      state.activeId = el.dataset.id;
      save(); renderAll();
    });
  });
  sessionsList.querySelectorAll('.sess-del').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.del;
      if (state.sessions.length <= 1) return;
      state.sessions = state.sessions.filter(s => s.id !== id);
      if (state.activeId === id) state.activeId = state.sessions[0].id;
      save(); renderAll();
    });
  });

  // Update partner name
  partnerNameEl.textContent = sess.name;
}

function renderPrompts() {
  const sess = active();
  girlNatureEl.value = sess.girlNature || '';
  boyNatureEl.value = sess.boyNature || '';
  charNotesEl.value = sess.notes || '';
  langSelect.value = sess.language || 'auto';
  relStage.value = sess.relStage || 'talking';
  
  const moodEmojis = { rizz: '✨', flirty: '💖', spicy: '🔥', neutral: '🍃', angry: '⚡', savage: '💀', mature: '🍷', dry: '🌵' };
  chatMoodLabel.textContent = `${moodEmojis[sess.mood] || '🍃'} ${sess.mood.charAt(0).toUpperCase() + sess.mood.slice(1)} Mode`;
}

function renderChat() {
  const sess = active();
  if (sess.messages.length === 0) {
    emptyState.classList.remove('hidden');
    chatMsgsEl.querySelectorAll('.msg').forEach(m => m.remove());
    return;
  }
  emptyState.classList.add('hidden');
  
  // Remove old messages
  chatMsgsEl.querySelectorAll('.msg').forEach(m => m.remove());
  
  sess.messages.forEach(m => {
    const div = document.createElement('div');
    div.className = `msg ${m.sender === 'user' ? 'out' : 'in'}`;
    
    let html = `<div>${escapeHtml(m.text)}</div>`;
    const time = m.time ? new Date(m.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
    html += `<div class="msg-meta"><span>${time}</span>${m.sender === 'user' ? '<span class="ticks">✓✓</span>' : ''}</div>`;
    
    if (m.rizzRating) {
      const cls = m.rizzRating.toLowerCase().includes('legend') ? 'legendary' : m.rizzRating.toLowerCase().includes('smooth') ? 'smooth' : m.rizzRating.toLowerCase().includes('decent') ? 'decent' : 'negative';
      html += `<span class="rizz-tag ${cls}">${m.rizzRating}</span>`;
    }
    
    div.innerHTML = html;
    chatMsgsEl.insertBefore(div, typingWrap);
  });

  // Scroll
  chatMsgsEl.scrollTop = chatMsgsEl.scrollHeight;
}

function renderMetrics() {
  const sess = active();
  const m = sess.metrics || {};
  
  psychBadge.textContent = (m.psychology || 'neutral').charAt(0).toUpperCase() + (m.psychology || 'neutral').slice(1);
  psychBadge.className = `psych-badge ${m.psychology || 'neutral'}`;
  psychText.textContent = m.psychologyText || 'Analyzing...';

  attractionPct.textContent = `${m.attraction || 70}%`;
  attractionFill.style.width = `${m.attraction || 70}%`;

  healthPct.textContent = m.conversationHealth ? `${m.conversationHealth}%` : '—';
  healthFill.style.width = `${m.conversationHealth || 50}%`;

  if (m.redFlags && m.redFlags.length > 0) {
    redFlagsArea.classList.remove('hidden');
    redFlagsList.innerHTML = m.redFlags.map(f => `<div>• ${escapeHtml(f)}</div>`).join('');
  } else {
    redFlagsArea.classList.add('hidden');
  }
}

function renderSentLog() {
  const sess = active();
  sentLogList.innerHTML = (sess.sentLog || []).slice(-10).map(item =>
    `<div class="sent-log-item">${escapeHtml(item.text)} <span style="font-size:8px; opacity:0.4;">${new Date(item.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>`
  ).join('');
}

function renderGraph() {
  const sess = active();
  const data = sess.attractionHistory || [70];
  if (data.length < 2) { attractSvg.innerHTML = ''; return; }
  
  const w = 300, h = 60, pad = 8;
  const stepX = (w - pad * 2) / (data.length - 1);
  
  let defs = `<defs><linearGradient id="grad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#7c3aed"/><stop offset="100%" stop-color="#e11d8f"/></linearGradient></defs>`;
  
  // Grid lines
  let grid = '';
  for (let i = 0; i <= 4; i++) {
    const y = pad + ((h - pad * 2) / 4) * i;
    grid += `<line x1="${pad}" y1="${y}" x2="${w - pad}" y2="${y}" class="graph-grid"/>`;
  }
  
  const points = data.map((v, i) => ({ x: pad + i * stepX, y: pad + (h - pad * 2) * (1 - v / 100) }));
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const dots = points.map((p, i) => `<circle cx="${p.x}" cy="${p.y}" r="3" class="graph-dot"><title>${data[i]}%</title></circle>`).join('');
  
  attractSvg.innerHTML = `${defs}${grid}<path d="${path}" class="graph-line"/>${dots}`;
}

function renderIcebreakers(category, lang) {
  iceCat = category || iceCat;
  iceLang = lang || iceLang;
  const langData = ICEBREAKERS[iceLang] || ICEBREAKERS.en;
  const items = langData[iceCat] || [];
  iceList.innerHTML = items.map(text => `<div class="ice-item">${escapeHtml(text)}</div>`).join('');
  iceList.querySelectorAll('.ice-item').forEach((el, i) => {
    el.addEventListener('click', () => {
      navigator.clipboard.writeText(items[i]).catch(() => {});
      el.style.borderColor = 'var(--green)';
      const orig = el.textContent;
      el.textContent = '✓ Copied!';
      playSound('select');
      setTimeout(() => { el.textContent = orig; el.style.borderColor = ''; }, 1200);
    });
  });
}

function updateMoodPills() {
  const sess = active();
  $$('.mood-pill').forEach(pill => {
    pill.classList.toggle('active', pill.dataset.mood === sess.mood);
  });
}

// ==================== API CARD RENDERING ====================
let lastPartnerMsg = '';

function renderSkeletons() {
  arenaCards.innerHTML = API_REGISTRY.map((api, i) => `
    <div class="skeleton-card" style="animation-delay: ${i * 0.06}s;">
      <div class="skeleton-badge"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
    </div>
  `).join('');
  arenaCounter.textContent = 'Loading...';
}

function renderApiCards(results) {
  let okCount = results.filter(r => r.status === 'ok').length;
  arenaCounter.textContent = `${okCount}/6 loaded`;

  arenaCards.innerHTML = results.map((r, i) => {
    if (r.status === 'error') {
      return `
        <div class="api-card error" style="animation-delay:${i * 0.06}s;">
          <div class="api-card-head">
            <span class="api-badge" style="background:${r.color}15; color:${r.color};">${r.apiName}</span>
          </div>
          <div class="api-response" style="color:var(--text-muted); font-style:italic;">⚠️ ${escapeHtml(r.error || 'Failed to generate')}</div>
        </div>
      `;
    }
    return `
      <div class="api-card" data-idx="${i}" style="animation-delay:${i * 0.06}s;">
        <div class="api-card-head">
          <span class="api-badge" style="background:${r.color}15; color:${r.color};">${r.apiName}</span>
          <div class="api-card-actions">
            <button class="icon-btn copy-card-btn" data-idx="${i}" title="Copy"><i data-lucide="copy"></i></button>
          </div>
        </div>
        <div class="api-response" id="resp-text-${i}">${escapeHtml(r.response)}</div>
        <div class="mod-row">
          <button class="mod-btn" data-idx="${i}" data-mod="rizz">✨ Rizz</button>
          <button class="mod-btn" data-idx="${i}" data-mod="humor">😂 Humor</button>
          <button class="mod-btn" data-idx="${i}" data-mod="shorten">✂️ Short</button>
          <button class="mod-btn" data-idx="${i}" data-mod="hinglish">🇮🇳 Hinglish</button>
        </div>
        <button class="select-btn" data-idx="${i}">
          <i data-lucide="check-circle"></i> Select as Reply
        </button>
      </div>
    `;
  }).join('');

  lucide.createIcons();
  bindCardEvents(results);
}

function bindCardEvents(results) {
  // Copy buttons
  arenaCards.querySelectorAll('.copy-card-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.idx);
      const text = results[idx]?.response || '';
      navigator.clipboard.writeText(text).catch(() => {});
      playSound('select');
    });
  });

  // Modifier buttons
  arenaCards.querySelectorAll('.mod-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.idx);
      const mod = btn.dataset.mod;
      const card = arenaCards.querySelector(`.api-card[data-idx="${idx}"]`);
      if (!card) return;
      card.classList.add('rewriting');
      try {
        const newText = await rewriteSuggestion(results[idx].response, mod);
        results[idx].response = newText;
        const respEl = card.querySelector('.api-response');
        if (respEl) respEl.textContent = newText;
      } catch (e) { console.error('Rewrite failed:', e); }
      card.classList.remove('rewriting');
    });
  });

  // Select buttons
  arenaCards.querySelectorAll('.select-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.idx);
      const text = results[idx]?.response;
      if (!text) return;
      selectResponse(text, results[idx]);
    });
  });
}

function selectResponse(text, cardResult) {
  const sess = active();
  
  // Add partner message if not already added
  if (lastPartnerMsg && (sess.messages.length === 0 || sess.messages[sess.messages.length - 1].text !== lastPartnerMsg)) {
    sess.messages.push({ sender: 'partner', text: lastPartnerMsg, time: Date.now() - 1000 });
  }
  
  // Add selected response as user's message
  sess.messages.push({ sender: 'user', text: text, time: Date.now(), apiSource: cardResult.apiName });
  playSound('send');
  save();
  renderChat();

  // Mark selected card
  arenaCards.querySelectorAll('.api-card').forEach(c => c.classList.remove('selected'));
  const selectedCard = arenaCards.querySelector(`.api-card[data-idx="${cardResult.apiId ? Array.from(arenaCards.querySelectorAll('.api-card')).findIndex(c => c.dataset.idx == arenaCards.querySelector(`[data-idx]`)?.dataset.idx) : '0'}"]`);
  
  // Find and highlight
  arenaCards.querySelectorAll('.api-card').forEach(c => {
    const respEl = c.querySelector('.api-response');
    if (respEl && respEl.textContent === text) c.classList.add('selected');
  });

  // Run background AI analysis
  runBackgroundAnalysis(lastPartnerMsg, text);
}

// ==================== AI ANALYSIS ====================
async function runBackgroundAnalysis(partnerMsg, userReply) {
  const sess = active();
  try {
    const analysis = await analyzeConversation(
      partnerMsg, userReply, sess.messages,
      sess.girlNature, sess.boyNature
    );
    if (analysis) {
      sess.metrics = {
        psychology: analysis.psychology || 'neutral',
        psychologyText: analysis.psychologyText || '',
        attraction: analysis.attraction || 70,
        rizzScore: analysis.rizzScore || 0,
        rizzRating: analysis.rizzRating || '',
        conversationHealth: analysis.conversationHealth || 50,
        redFlags: analysis.redFlags || [],
        moodSuggestion: analysis.moodSuggestion || ''
      };
      sess.attractionHistory.push(analysis.attraction || 70);
      if (analysis.relationshipStage) sess.relStage = analysis.relationshipStage;
      
      // Apply rizz rating to last user message
      const lastMsg = sess.messages.filter(m => m.sender === 'user').pop();
      if (lastMsg && analysis.rizzRating) lastMsg.rizzRating = analysis.rizzRating;

      save();
      renderMetrics();
      renderGraph();
      renderChat(); // Re-render for rizz tags
    }
  } catch (e) { console.error('Analysis error:', e); }
}

// ==================== EVENTS ====================
function init() {
  // --- Onboarding: Show on first visit ---
  if (!state.onboarded) {
    const onboardModal = $('#onboard-modal');
    onboardModal.classList.remove('hidden');
    $('#onboard-start').addEventListener('click', () => {
      const boyName = $('#onboard-boy').value.trim() || 'You';
      const girlName = $('#onboard-girl').value.trim() || 'Chloe';
      state = defaultState(boyName, girlName);
      save();
      onboardModal.classList.add('hidden');
      init(); // Re-initialize with full event binding
    });
    // Allow pressing Enter to start
    $('#onboard-girl').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); $('#onboard-start').click(); }
    });
    $('#onboard-boy').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        $('#onboard-girl').focus();
      }
    });
    lucide.createIcons();
    return; // Don't render the main app yet
  }

  renderAll();

  // --- Generate All ---
  genBtn.addEventListener('click', async () => {
    const msg = partnerMsgEl.value.trim();
    if (!msg) return;
    lastPartnerMsg = msg;
    genBtn.disabled = true;
    genBtn.innerHTML = '<div class="spinner" style="width:14px;height:14px;border-width:2px;"></div> Generating...';
    renderSkeletons();
    
    try {
      const sess = active();
      const results = await generateAllParallel(
        msg, sess.messages, sess.mood,
        sess.girlNature, sess.boyNature,
        sess.language
      );
      renderApiCards(results);
      regenBtn.disabled = false;
    } catch (e) {
      arenaCards.innerHTML = `<div style="text-align:center; padding:20px; color:var(--red); font-size:11px;">All APIs failed. Please try again.</div>`;
      console.error('Generate error:', e);
    }
    
    genBtn.disabled = false;
    genBtn.innerHTML = '<i data-lucide="zap"></i> Generate All Responses';
    lucide.createIcons();
  });

  // --- Regenerate with Feedback ---
  regenBtn.addEventListener('click', async () => {
    const feedback = feedbackInput.value.trim();
    if (!feedback || !lastPartnerMsg) return;
    regenBtn.disabled = true;
    regenBtn.innerHTML = '<div class="spinner" style="width:12px;height:12px;border-width:2px;"></div> Regenerating...';
    renderSkeletons();

    try {
      const sess = active();
      const results = await generateAllParallel(
        lastPartnerMsg, sess.messages, sess.mood,
        sess.girlNature, sess.boyNature,
        sess.language, feedback
      );
      renderApiCards(results);
      feedbackInput.value = '';
    } catch (e) {
      arenaCards.innerHTML = `<div style="text-align:center; padding:20px; color:var(--red); font-size:11px;">Regeneration failed. Try again.</div>`;
    }

    regenBtn.disabled = false;
    regenBtn.innerHTML = '<i data-lucide="refresh-cw"></i> Regenerate with Feedback';
    lucide.createIcons();
  });

  // --- Feedback input enables regen button ---
  feedbackInput.addEventListener('input', () => {
    regenBtn.disabled = !feedbackInput.value.trim();
  });

  // --- Log What I Actually Sent ---
  $('#log-sent-btn').addEventListener('click', () => {
    const text = actualSentEl.value.trim();
    if (!text) return;
    const sess = active();
    sess.sentLog.push({ text, time: Date.now() });
    actualSentEl.value = '';
    save();
    renderSentLog();
    playSound('send');
  });
  actualSentEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); $('#log-sent-btn').click(); }
  });

  // --- Mood Pills ---
  $$('.mood-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      active().mood = pill.dataset.mood;
      save();
      updateMoodPills();
      renderPrompts();
    });
  });

  // --- Prompt Saving (auto-save on blur) ---
  girlNatureEl.addEventListener('blur', () => { active().girlNature = girlNatureEl.value; save(); });
  boyNatureEl.addEventListener('blur', () => { active().boyNature = boyNatureEl.value; save(); });
  charNotesEl.addEventListener('blur', () => { active().notes = charNotesEl.value; save(); });
  langSelect.addEventListener('change', () => { active().language = langSelect.value; save(); });
  relStage.addEventListener('change', () => { active().relStage = relStage.value; save(); });

  // --- Icebreaker Category Tabs ---
  $$('.ice-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.ice-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderIcebreakers(tab.dataset.cat, iceLang);
    });
  });

  // --- Icebreaker Language Tabs ---
  $$('.ice-lang-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.ice-lang-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderIcebreakers(iceCat, tab.dataset.lang);
    });
  });

  // --- Sandbox Mode ---
  sandboxToggle.addEventListener('change', () => {
    const isOn = sandboxToggle.checked;
    sandboxForm.classList.toggle('hidden', !isOn);
    chatLabel.classList.toggle('hidden', isOn);
  });

  sandboxForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = sandboxInput.value.trim();
    if (!text) return;
    const sess = active();
    sess.messages.push({ sender: 'user', text, time: Date.now() });
    sandboxInput.value = '';
    playSound('send');
    save(); renderChat();

    // Show typing
    typingWrap.classList.add('show');
    try {
      const reply = await generatePartnerReply(text, sess.messages, sess.girlNature, sess.mood);
      sess.messages.push({ sender: 'partner', text: reply, time: Date.now() });
      playSound('receive');
      save(); renderChat();
    } catch (e) { console.error('Partner reply error:', e); }
    typingWrap.classList.remove('show');
  });

  // --- Create Character ---
  $('#create-char-btn').addEventListener('click', () => {
    $('#create-modal').classList.remove('hidden');
    $('#create-name').value = ''; $('#create-nature').value = '';
  });
  $('#create-cancel').addEventListener('click', () => $('#create-modal').classList.add('hidden'));
  $('#create-save').addEventListener('click', () => {
    const name = $('#create-name').value.trim() || 'New Character';
    const gender = $('#create-gender').value;
    const nature = $('#create-nature').value.trim();
    const id = 'char_' + Date.now();
    state.sessions.push({
      id, name, gender,
      girlNature: nature || 'Friendly and engaging personality.',
      boyNature: active().boyNature || '',
      mood: 'rizz', language: 'auto', notes: '',
      messages: [], attractionHistory: [70], sentLog: [],
      metrics: { psychology: 'neutral', psychologyText: 'Analyzing...', attraction: 70, rizzScore: 0, rizzRating: '', conversationHealth: 50, redFlags: [], moodSuggestion: '' },
      relStage: 'stranger'
    });
    state.activeId = id;
    save(); renderAll();
    $('#create-modal').classList.add('hidden');
  });

  // --- Edit Partner ---
  $('#edit-btn').addEventListener('click', () => {
    const sess = active();
    $('#edit-name').value = sess.name;
    $('#edit-gender').value = sess.gender;
    $('#edit-modal').classList.remove('hidden');
  });
  $('#edit-cancel').addEventListener('click', () => $('#edit-modal').classList.add('hidden'));
  $('#edit-save').addEventListener('click', () => {
    const sess = active();
    sess.name = $('#edit-name').value.trim() || sess.name;
    sess.gender = $('#edit-gender').value;
    save(); renderAll();
    $('#edit-modal').classList.add('hidden');
  });

  // --- Import History ---
  $('#import-btn').addEventListener('click', () => {
    $('#history-input').value = '';
    $('#history-modal').classList.remove('hidden');
    lucide.createIcons();
  });

  // File drop zone
  const dropZone = $('#drop-zone');
  const fileInput = $('#file-input');

  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--accent)';
    dropZone.style.background = 'rgba(124,58,237,0.05)';
  });
  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--border)';
    dropZone.style.background = 'transparent';
  });
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border)';
    dropZone.style.background = 'transparent';
    const file = e.dataTransfer.files[0];
    if (file) readChatFile(file);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) readChatFile(fileInput.files[0]);
    fileInput.value = ''; // Reset so same file can be selected again
  });

  function readChatFile(file) {
    if (!file.name.endsWith('.txt') && !file.name.endsWith('.text')) {
      alert('Please drop a .txt file (WhatsApp chat export).');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      $('#history-input').value = content;
      // Update drop zone to show success
      dropZone.innerHTML = `<p style="font-size:12px; color:var(--green);">\u2705 ${file.name} loaded (${content.split('\n').length} lines)</p><p style="font-size:9px; color:var(--text-muted);">Click "Import & Analyze" to proceed</p>`;
    };
    reader.readAsText(file);
  }
  $('#history-cancel').addEventListener('click', () => $('#history-modal').classList.add('hidden'));
  $('#history-save').addEventListener('click', () => {
    const raw = $('#history-input').value.trim();
    if (!raw) return;
    const sess = active();
    const boyName = (state.boyName || 'You').toLowerCase();
    const partnerName = sess.name.toLowerCase();
    
    // Build list of names that count as "you" (the user/boy)
    const userAliases = new Set(['you', 'me', "i'm", 'i', 'mein', 'main', boyName]);
    
    const lines = raw.split('\n').filter(l => l.trim());
    const parsed = lines.map(line => {
      // Strip WhatsApp date/time: [29/05, 2:48 pm] or similar
      let cleaned = line.replace(/^\[.*?\]\s*/, '');
      
      // Find the sender:message split (first colon)
      const colonIdx = cleaned.indexOf(':');
      if (colonIdx === -1 || colonIdx > 50) return null; // No sender found or sender name too long
      
      const senderRaw = cleaned.slice(0, colonIdx).trim();
      const text = cleaned.slice(colonIdx + 1).trim();
      if (!text) return null; // Empty message
      
      // Check if this sender is the user (boy)
      const senderLow = senderRaw.toLowerCase();
      const isUser = userAliases.has(senderLow) || senderLow.includes(boyName);
      
      return { sender: isUser ? 'user' : 'partner', text, time: Date.now() };
    }).filter(Boolean);
    
    if (parsed.length === 0) {
      alert('Could not parse any messages. Make sure each line has "Name: message" format.');
      return;
    }
    
    sess.messages = parsed;
    save(); renderChat();
    $('#history-modal').classList.add('hidden');
    
    // Show count
    const userCount = parsed.filter(m => m.sender === 'user').length;
    const partnerCount = parsed.filter(m => m.sender === 'partner').length;
    console.log(`Imported: ${parsed.length} messages (${userCount} from you, ${partnerCount} from ${sess.name})`);
  });

  // --- Clear Chat ---
  $('#clear-btn').addEventListener('click', () => {
    if (!confirm('Clear all chat messages for this session?')) return;
    const sess = active();
    sess.messages = [];
    sess.attractionHistory = [70];
    sess.metrics = { psychology: 'neutral', psychologyText: 'Analyzing...', attraction: 70, rizzScore: 0, rizzRating: '', conversationHealth: 50, redFlags: [], moodSuggestion: '' };
    save(); renderAll();
  });

  // --- Sound Toggle ---
  $('#sound-btn').addEventListener('click', () => {
    state.soundOn = !state.soundOn;
    $('#sound-btn').innerHTML = `<i data-lucide="${state.soundOn ? 'volume-2' : 'volume-x'}"></i> ${state.soundOn ? 'Sound' : 'Muted'}`;
    save(); lucide.createIcons();
  });

  // --- Export ---
  $('#export-btn').addEventListener('click', () => {
    const sess = active();
    const text = sess.messages.map(m => `${m.sender === 'user' ? 'You' : sess.name}: ${m.text}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `aura-chat-${sess.name}-${Date.now()}.txt`;
    a.click(); URL.revokeObjectURL(url);
  });

  // --- Reset ---
  $('#reset-btn').addEventListener('click', () => {
    if (!confirm('⚠️ Reset ALL data? This cannot be undone.')) return;
    localStorage.removeItem(STORAGE_KEY);
    location.reload();
  });

  // --- Coach Report ---
  $('#coach-btn').addEventListener('click', async () => {
    const sess = active();
    $('#coach-modal').classList.remove('hidden');
    $('#coach-loading').classList.remove('hidden');
    $('#coach-content').style.display = 'none';

    try {
      const report = await generateCoachReport(sess.messages, sess.girlNature, sess.boyNature);
      $('#coach-grade').textContent = report.grade || 'B+';
      $('#coach-summary').textContent = report.summary || '';
      
      $('#stat-a').style.width = `${report.charisma || 70}%`; $('#stat-a-val').textContent = `${report.charisma || 70}%`;
      $('#stat-b').style.width = `${report.empathy || 70}%`; $('#stat-b-val').textContent = `${report.empathy || 70}%`;
      $('#stat-c').style.width = `${report.tension || 50}%`; $('#stat-c-val').textContent = `${report.tension || 50}%`;
      $('#stat-d').style.width = `${report.confidence || 60}%`; $('#stat-d-val').textContent = `${report.confidence || 60}%`;

      $('#coach-wins').innerHTML = (report.wins || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');
      $('#coach-fumbles').innerHTML = (report.fumbles || []).map(f => `<li>${escapeHtml(f)}</li>`).join('');
      $('#coach-rec-line').textContent = report.recommendation || '';
    } catch (e) { console.error('Coach report error:', e); }

    $('#coach-loading').classList.add('hidden');
    $('#coach-content').style.display = 'block';
    lucide.createIcons();
  });

  $('#coach-close').addEventListener('click', () => $('#coach-modal').classList.add('hidden'));
  $('#coach-copy').addEventListener('click', () => {
    navigator.clipboard.writeText($('#coach-rec-line').textContent).catch(() => {});
    playSound('select');
  });

  // --- Mobile Tabs ---
  $('#tab-left').addEventListener('click', () => {
    document.body.classList.add('show-left');
    document.body.classList.remove('show-right');
    $$('.mob-tab').forEach(t => t.classList.remove('active'));
    $('#tab-left').classList.add('active');
  });
  $('#tab-center').addEventListener('click', () => {
    document.body.classList.remove('show-left', 'show-right');
    $$('.mob-tab').forEach(t => t.classList.remove('active'));
    $('#tab-center').classList.add('active');
  });
  $('#tab-right').addEventListener('click', () => {
    document.body.classList.remove('show-left');
    document.body.classList.add('show-right');
    $$('.mob-tab').forEach(t => t.classList.remove('active'));
    $('#tab-right').classList.add('active');
  });

  // --- Close modals on overlay click ---
  $$('.modal-bg').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.add('hidden');
    });
  });

  // --- Keyboard: Enter on partner msg triggers generate ---
  partnerMsgEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      genBtn.click();
    }
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Start
init();
