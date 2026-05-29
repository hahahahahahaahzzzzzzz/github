/**
 * Aura Chat v3 — API Integration Layer
 * 
 * Core feature: generateAllParallel() fires all 6 AI endpoints simultaneously.
 * Each returns a labeled card result. User picks the best one.
 * Supports feedback-based regeneration.
 */

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// --- CORS Proxy Fallbacks ---
const PROXIES = [
  (url) => `https://corsproxy.io/?${encodeURIComponent(url)}`,
  (url) => `https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(url)}`,
  (url) => `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`,
];

async function fetchWithTimeout(url, timeoutMs = 20000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    return res;
  } catch (e) {
    clearTimeout(timer);
    throw e;
  }
}

async function fetchWithFallback(targetUrl, label = 'API') {
  // 1. Try direct
  try {
    const res = await fetchWithTimeout(targetUrl, 15000);
    if (res && res.ok) return res;
  } catch (e) {
    console.warn(`[${label}] Direct failed:`, e.message);
  }
  // 2. Try each proxy
  for (let i = 0; i < PROXIES.length; i++) {
    try {
      const proxyUrl = PROXIES[i](targetUrl);
      console.log(`[${label}] Trying proxy ${i + 1}...`);
      const res = await fetchWithTimeout(proxyUrl, 18000);
      if (res && res.ok) return res;
    } catch (e) {
      console.warn(`[${label}] Proxy ${i + 1} failed:`, e.message);
    }
  }
  return null;
}

// --- API Endpoint Registry ---
const API_REGISTRY = [
  { id: 'gpt5', name: 'GPT-5', url: 'https://apis.prexzyvilla.site/ai/gpt-5', param: 'text', color: '#10b981' },
  { id: 'copilot-think', name: 'Copilot Think', url: 'https://apis.prexzyvilla.site/ai/copilot-think', param: 'text', color: '#8b5cf6' },
  { id: 'copilot', name: 'Copilot', url: 'https://apis.prexzyvilla.site/ai/copilot', param: 'text', color: '#3b82f6' },
  { id: 'ai4chat', name: 'AI4Chat', url: 'https://apis.prexzyvilla.site/ai/ai4chat', param: 'prompt', color: '#f59e0b' },
  { id: 'aiserv', name: 'AiServ', url: 'https://apis.prexzyvilla.site/ai/aiserv', param: 'prompt', color: '#ef4444' },
  { id: 'chatex', name: 'ChatEx', url: 'https://apis.prexzyvilla.site/ai/chatex', param: 'text', color: '#ec4899' }
];

// --- Response Parser (handles all API response formats) ---
function extractResponseText(bodyText) {
  let text = bodyText;
  try {
    const parsed = JSON.parse(bodyText);
    if (parsed.contents) {
      // allorigins proxy wrapper
      try {
        const inner = JSON.parse(parsed.contents);
        if (inner.data && inner.data.response) return inner.data.response;
        if (inner.response) return inner.response;
        if (inner.text) return inner.text;
        return parsed.contents;
      } catch (e) {
        return parsed.contents;
      }
    }
    if (parsed.data && parsed.data.response) return parsed.data.response;
    if (parsed.response) return parsed.response;
    if (parsed.text) return parsed.text;
  } catch (e) {
    // Not JSON, use raw text
  }
  return text;
}

// --- Strip AI disclaimers from responses ---
function cleanAiDisclaimer(text) {
  if (!text) return text;
  
  // Common AI preamble patterns to strip
  const disclaimerPatterns = [
    // "Sorry—I can't pretend to be an actual human. I can, however, roleplay..."
    /^sorry[\s—\-–,]+i\s+can'?t\s+(pretend|claim|act|be).*?(however|but|instead|here'?s?|that said)[,.\s—\-–]*/i,
    // "As an AI, I can't... but here's..."
    /^as\s+an?\s+(ai|artificial|language\s+model|chatbot).*?(however|but|here'?s?|that said)[,.\s—\-–]*/i,
    // "I'm an AI, so I can't... but..."
    /^i'?m\s+an?\s+(ai|artificial|language\s+model).*?(however|but|here'?s?|that said)[,.\s—\-–]*/i,
    // "I can't pretend to be human, but..."
    /^i\s+can'?t\s+(pretend|claim|act|be).*?(however|but|here'?s?|that said|i can)[,.\s—\-–]*/i,
    // "Sure, here's a reply:" or "Here's what the character would say:"
    /^(sure|okay|alright|of course)[!.,\s]*(here'?s?|i'?ll).*?(reply|response|message|say|text)[:\s—\-–]*/i,
    // "Here's a casual reply:" 
    /^here'?s?\s+(a\s+)?(casual|natural|the|your|my).*?(reply|response|message|text)[:\s—\-–]*/i,
    // "[Character name]'s reply:" or "The character would reply:"
    /^(the\s+)?character('?s?)?\s+(would\s+)?(reply|respond|say|text)[:\s—\-–]*/i,
    // "In this roleplay scenario..."
    /^in\s+this\s+(roleplay|scenario|creative|scene).*?[:\s—\-–]+/i,
  ];
  
  let cleaned = text;
  for (const pattern of disclaimerPatterns) {
    cleaned = cleaned.replace(pattern, '').trim();
  }
  
  // Also remove leading ** markdown bold ** wrappers
  cleaned = cleaned.replace(/^\*\*(.+?)\*\*$/s, '$1').trim();
  
  // Remove leading/trailing quotes that some AIs add
  cleaned = cleaned.replace(/^["'""]|["'""]$/g, '').trim();
  
  return cleaned || text; // Fallback to original if everything got stripped
}

// --- Language Auto-Detection ---
function detectLanguage(text, selectedLang) {
  if (selectedLang !== 'auto') return selectedLang;
  const isHindiUnicode = /[\u0900-\u097F]/.test(text);
  const isHinglish = /\b(kya|kar|rha|kuch|hai|yaar|tum|toh|aaj|chal|batao|kese|kaise|haan|nhi|nahi|hi|bye|aur|bata|rhi|ho|tha|rhe|hote|bhai|accha|sahi)\b/i.test(text);
  if (isHindiUnicode) return 'hindi';
  if (isHinglish) return 'hinglish';
  return 'english';
}

function getLangInstruction(lang) {
  if (lang === 'hinglish') return 'Hinglish (Hindi written in Roman/English script like "Main badhiya hu, tum batao?")';
  if (lang === 'hindi') return 'Hindi (in Devanagari script)';
  return 'English';
}

// --- Build the master prompt ---
function buildSuggestionPrompt(partnerMessage, history, mood, girlNature, boyNature, language, feedback) {
  const langText = getLangInstruction(language);
  
  const moodGuide = {
    rizz: 'charming, smooth, confident, uses clever wordplay, makes them feel special, never tries too hard',
    flirty: 'sweet, teasing, affectionate, compliments naturally, adds cute touches, makes them smile',
    spicy: 'bold, passionate, suggestive, builds tension and chemistry, seductive but not creepy',
    neutral: 'casual, chill, friendly, keeps it real and relaxed, normal everyday texting',
    angry: 'frustrated, short, defensive, expresses annoyance, leave-them-on-read energy',
    savage: 'sarcastic, witty, sharp, roasts playfully, no filter but all in fun',
    mature: 'thoughtful, emotionally intelligent, deep, meaningful, makes them feel heard',
    dry: 'minimal, unbothered, cold, short replies, one word answers, dry texter energy'
  };

  const chatHistory = history.slice(-8).map(h => `${h.sender === 'user' ? 'You' : 'Them'}: ${h.text}`).join('\n');

  let prompt = `[CREATIVE WRITING TASK — Write dialogue for a texting scene]

Write the next text message reply for a character in a casual WhatsApp/Instagram conversation.

CHARACTER PROFILE (the person replying):
${boyNature}

THE OTHER PERSON IN THE CHAT:
${girlNature}

CHARACTER'S CURRENT TEXTING VIBE: ${moodGuide[mood] || moodGuide.neutral}

CONVERSATION SO FAR:
${chatHistory || '(First message in the conversation)'}

THE OTHER PERSON JUST SENT:
"${partnerMessage}"

Write the character's reply message.`;

  if (feedback) {
    prompt += `

NOTE: Previous draft was rejected. Writer's note: "${feedback}"
Write a completely different reply based on this note.`;
  }

  prompt += `

WRITING GUIDELINES:
- Write ONLY the message text. No stage directions, no quotes, no labels, no "Reply:" prefix.
- Keep it natural and casual like real texting: lowercase ok, short sentences, casual grammar.
- DO NOT reference spelling mistakes or how they typed. Just respond to the meaning.
- Match their message length. Short message = short reply. Long = can be longer.
- Emojis are ok but use sparingly and naturally.
- If they write in Hindi/Hinglish, reply in the same language.
- Language: ${langText}
- Output ONLY the chat message. Nothing else. No explanations.`;

  return prompt;
}


/**
 * CORE: Fire all 6 APIs in parallel. Returns array of results.
 * Each result: { apiId, apiName, color, status: 'ok'|'error', response: string, error?: string }
 */
export async function generateAllParallel(partnerMessage, history, mood, girlNature, boyNature, language = 'auto', feedback = '') {
  const targetLang = detectLanguage(partnerMessage, language);
  const prompt = buildSuggestionPrompt(partnerMessage, history, mood, girlNature, boyNature, targetLang, feedback);

  const promises = API_REGISTRY.map(async (api) => {
    const targetUrl = `${api.url}?${api.param}=${encodeURIComponent(prompt)}`;
    try {
      const res = await fetchWithFallback(targetUrl, api.name);

      if (res) {
        const bodyText = await res.text();
        let responseText = extractResponseText(bodyText);
        // Clean markdown artifacts
        responseText = responseText.replace(/```[a-z]*/gi, '').replace(/```/g, '').trim();
        responseText = responseText.replace(/^["']|["']$/g, '').trim();
        // Remove "Reply:" or "Suggestion:" prefixes
        responseText = responseText.replace(/^(Reply|Suggestion|Response|Answer|Here's?|Sure|Okay|Character'?s? reply)\s*[:\-—]\s*/i, '').trim();
        // Strip AI disclaimers / safety preambles
        responseText = cleanAiDisclaimer(responseText);
        
        if (responseText && responseText.length > 0 && responseText.length < 2000) {
          return { apiId: api.id, apiName: api.name, color: api.color, status: 'ok', response: responseText };
        }
      }
      return { apiId: api.id, apiName: api.name, color: api.color, status: 'error', response: '', error: 'No valid response from any endpoint' };
    } catch (err) {
      return { apiId: api.id, apiName: api.name, color: api.color, status: 'error', response: '', error: err.message };
    }
  });

  const results = await Promise.allSettled(promises);
  return results.map(r => r.status === 'fulfilled' ? r.value : { apiId: 'unknown', apiName: 'Unknown', color: '#666', status: 'error', response: '', error: 'Promise rejected' });
}

/**
 * Rewrite a suggestion with a modifier (rizz, humor, shorten, hindi, hinglish)
 */
export async function rewriteSuggestion(text, option, model = 'gpt5') {
  await sleep(300 + Math.random() * 400);
  const api = API_REGISTRY.find(a => a.id === model) || API_REGISTRY[0];

  let instruction = '';
  if (option === 'rizz') instruction = 'Add strong rizz, charisma, and make it sound smooth, charming and flirty.';
  else if (option === 'humor') instruction = 'Add humor, playful teasing, or light sarcasm.';
  else if (option === 'shorten') instruction = 'Make it much shorter and punchier (under 40 characters).';
  else if (option === 'hindi') instruction = 'Translate into pure Hindi (Devanagari script).';
  else if (option === 'hinglish') instruction = 'Translate into Hinglish (Hindi in Roman/English script).';

  const prompt = `Rewrite this text: "${text}"\nDirective: ${instruction}\nOutput ONLY the rewritten text. No quotes, no explanations.`;
  const targetUrl = `${api.url}?${api.param}=${encodeURIComponent(prompt)}`;

  try {
    let res = await fetch(targetUrl).catch(() => fetch(`https://api.allorigins.win/get?url=${encodeURIComponent(targetUrl)}`));
    if (res && res.ok) {
      const body = await res.text();
      let result = extractResponseText(body).replace(/```[a-z]*/gi, '').replace(/```/g, '').replace(/^["']|["']$/g, '').trim();
      if (result && result.length > 0) return result;
    }
  } catch (e) { console.error('Rewrite failed:', e); }

  // Fallback
  const fallbacks = { rizz: text + ' 😉', humor: text + ' (haha)', shorten: text.slice(0, 30) + '...', hindi: 'क्या हाल चाल?', hinglish: 'Aur batao kya chal rha?' };
  return fallbacks[option] || text;
}

/**
 * Analyze conversation metrics via AI
 */
export async function analyzeConversation(partnerMessage, userReply, history, girlNature, boyNature, model = 'gpt5') {
  const api = API_REGISTRY.find(a => a.id === model) || API_REGISTRY[0];

  const prompt = `Analyze this conversation exchange.
Character nature: "${girlNature}"
User identity: "${boyNature}"
History: ${JSON.stringify(history.slice(-8).map(h => ({ sender: h.sender, text: h.text })))}
Partner said: "${partnerMessage}"
User replied: "${userReply}"

Return EXACTLY a JSON object (no markdown, no code blocks):
{
  "psychology": "interested" or "neutral" or "dry",
  "psychologyText": "1-sentence analysis of their interest level",
  "attraction": 0 to 100,
  "rizzScore": 0 to 100,
  "rizzRating": "Legendary Rizz" or "Smooth Rizz" or "Decent Aura" or "Negative Rizz",
  "relationshipStage": "stranger" or "talking" or "friends" or "flirting" or "bond" or "relationship",
  "moodSuggestion": "best mood mode to use next (rizz/flirty/spicy/neutral/angry/savage/mature/dry)",
  "conversationHealth": 0 to 100,
  "redFlags": ["any manipulative or toxic patterns detected"] or []
}`;

  const targetUrl = `${api.url}?${api.param}=${encodeURIComponent(prompt)}`;
  try {
    let res = await fetch(targetUrl).catch(() => fetch(`https://api.allorigins.win/get?url=${encodeURIComponent(targetUrl)}`));
    if (res && res.ok) {
      let body = await res.text();
      body = extractResponseText(body);
      body = body.replace(/```json/gi, '').replace(/```/g, '').trim();
      const analysis = JSON.parse(body);
      if (analysis && typeof analysis.attraction === 'number') return analysis;
    }
  } catch (e) { console.error('Analysis failed:', e); }
  return null;
}

/**
 * Generate coach report card
 */
export async function generateCoachReport(history, girlNature, boyNature, model = 'gpt5') {
  await sleep(800);
  const api = API_REGISTRY.find(a => a.id === model) || API_REGISTRY[0];

  const prompt = `Analyze this chat between User and Partner.
Partner Nature: "${girlNature}"
User Identity: "${boyNature}"
Chat: ${JSON.stringify(history.slice(-15).map(h => ({ sender: h.sender, text: h.text })))}

Return EXACTLY JSON (no markdown):
{
  "grade": "A+ to F letter grade",
  "wins": ["positive point 1", "positive point 2"],
  "fumbles": ["mistake 1", "mistake 2"],
  "charisma": 0-100, "empathy": 0-100, "tension": 0-100, "confidence": 0-100,
  "summary": "2-sentence review",
  "recommendation": "exact next line to send"
}`;

  const targetUrl = `${api.url}?${api.param}=${encodeURIComponent(prompt)}`;
  try {
    let res = await fetch(targetUrl).catch(() => fetch(`https://api.allorigins.win/get?url=${encodeURIComponent(targetUrl)}`));
    if (res && res.ok) {
      let body = extractResponseText(await res.text()).replace(/```json/gi, '').replace(/```/g, '').trim();
      const report = JSON.parse(body);
      if (report && report.grade) return report;
    }
  } catch (e) { console.error('Coach report failed:', e); }

  return {
    grade: 'B+', wins: ['Kept the conversation active', 'Asked engaging questions'],
    fumbles: ['Replying too fast', 'Could use more playful teasing'],
    charisma: 72, empathy: 78, tension: 60, confidence: 68,
    summary: 'Solid communication but leans friendly over romantic. Add more tension.',
    recommendation: 'Try teasing them about their late replies or suggest meeting up.'
  };
}

/**
 * Generate partner auto-reply for sandbox mode
 */
export async function generatePartnerReply(message, history, nature, mood, model = 'gpt5') {
  await sleep(1000 + Math.random() * 800);
  const api = API_REGISTRY.find(a => a.id === model) || API_REGISTRY[0];

  const prompt = `You are roleplaying as a character in a chat.
Your personality: "${nature}"
Your mood: "${mood}"
History: ${JSON.stringify(history.slice(-8).map(h => ({ sender: h.sender, text: h.text })))}
User just said: "${message}"

Reply in character. Output ONLY your message. No quotes, no labels.
If the user writes in Hinglish/Hindi, respond in the same language.`;

  const targetUrl = `${api.url}?${api.param}=${encodeURIComponent(prompt)}`;
  try {
    let res = await fetch(targetUrl).catch(() => fetch(`https://api.allorigins.win/get?url=${encodeURIComponent(targetUrl)}`));
    if (res && res.ok) {
      let result = extractResponseText(await res.text()).replace(/```[a-z]*/gi, '').replace(/```/g, '').replace(/^["']|["']$/g, '').trim();
      if (result && result.length > 0) return result;
    }
  } catch (e) { console.error('Partner reply failed:', e); }

  const fallbacks = {
    rizz: ["You always know what to say, don't you?", "Well that was smooth.", "I'm impressed."],
    flirty: ["Aww you're making me blush 🤭", "I was just thinking about you!", "What would you do if I was there?"],
    spicy: ["You shouldn't say that unless you mean it...", "It's getting warm in here.", "Tell me more..."],
    angry: ["Why are you acting like nothing happened?", "I don't care. Do whatever.", "You're annoying."],
    neutral: ["Oh cool! What next?", "Nice. I'm just chilling.", "That makes sense."],
    savage: ["Is that the best you got?", "Aww look at you trying.", "Disappointing."],
    mature: ["I appreciate that. It's refreshing.", "Life's too short for games.", "Easy to talk to you."],
    dry: ["Ok.", "Hmm.", "K."]
  };
  const pool = fallbacks[mood] || fallbacks.neutral;
  return pool[Math.floor(Math.random() * pool.length)];
}

export { API_REGISTRY };
