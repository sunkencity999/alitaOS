#!/usr/bin/env python3
"""
Ollama Live Assistant Component
Provides real-time voice conversation using local Ollama models.

Uses:
- Streamlit text input for user messages
- Ollama streaming for AI responses  
- Browser Speech Synthesis API for text-to-speech
"""

import streamlit as st
import base64
import os
from pathlib import Path
from utils.ai_models import get_llm

def display_ollama_live_assistant():
    """Display the Ollama-powered live assistant interface."""
    
    # Get current AI provider and model
    ai_provider = st.session_state.get('ai_provider', 'openai')
    ai_model = st.session_state.get('ai_model', 'gpt-4o-mini')
    
    # Initialize conversation history
    if 'ollama_conversation' not in st.session_state:
        st.session_state.ollama_conversation = []
    
    # Only show if Ollama is selected
    if ai_provider != 'ollama':
        st.warning("**Local Live Assistant** requires Ollama to be selected in AI Settings.")
        return

    # Get app directory for avatar
    app_dir = Path(__file__).parent.parent
    
    # Load avatar image from common locations and formats, prefer app/static/alita.*
    avatar_src = "https://placehold.co/144x144/667eea/ffffff?text=A"
    candidate_paths = [
        app_dir / "static" / "alita.jpg",
        app_dir / "static" / "alita.jpeg",
        app_dir / "static" / "alita.png",
        app_dir / "public" / "avatars" / "alita.jpg",
        app_dir / "public" / "avatars" / "alita.png",
        app_dir / "public" / "avatars" / "my-assistant.png",
        app_dir.parent / "images" / "thumbnail_short_demo.png",
    ]
    for p in candidate_paths:
        try:
            if p.exists():
                with open(p, "rb") as f:
                    img_bytes = f.read()
                # Guess content type from suffix
                suffix = p.suffix.lower().lstrip('.') or 'jpeg'
                if suffix == 'jpg':
                    suffix = 'jpeg'
                b64 = base64.b64encode(img_bytes).decode("ascii")
                avatar_src = f"data:image/{suffix};base64,{b64}"
                break
        except Exception:
            continue

    # Decide default search provider based on env (Tavily if key present)
    provider_default = "tavily" if os.getenv("TAVILY_API_KEY") else "auto"

    # Header
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #666; margin-bottom: 5px;">🎧 Live Assistant</h2>
            <p style="color: #888; font-size: 14px; margin-bottom: 20px;">Click Start to grant mic access. Bi-directional low-latency voice.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Provide Start/Stop UI with transcript and animated avatar
    st.components.v1.html(
            fr"""
<style>
  :root {{
    /* inherit globals from page: light theme */
  }}
  html, body {{ margin:0; padding:0; overflow: visible; }}
  #outer {{ width:100%; display:block; text-align:center; }}
  #container {{
    margin: 0 auto !important; width: 100%; max-width: 1060px; background: var(--panel); padding: 20px 24px; border-radius: 12px; border:1px solid var(--border);
    display: inline-block; text-align: initial; overflow: visible; box-sizing: border-box;
  }}
  #avatar-row {{ display:flex; justify-content:center; align-items:center; margin-bottom:16px; }}
  #avatar {{ width:84px; height:84px; border-radius:50%; object-fit:cover; box-shadow:0 0 0px rgba(34,197,94,0.0); transition: box-shadow 160ms ease; border:2px solid var(--border); background:#ddd; display:block; }}
  #avatar.speaking {{ box-shadow:0 0 22px rgba(34,197,94,0.55); }}
  #avatar.listening {{ box-shadow:0 0 22px rgba(59,130,246,0.55); }}
  #buttons-row {{ display:flex; justify-content:center; align-items:center; gap:12px; margin-bottom:12px; }}
  #settings-row {{ display:flex; justify-content:center; align-items:center; gap:12px; margin-bottom:14px; text-align:center; }}
  #buttons-row button {{
    -webkit-appearance:none; appearance:none; border:1px solid #1f232b !important; padding:10px 20px; border-radius:12px; font-weight:600; cursor:pointer;
    color:#fff !important; background:#2b2f36 !important; min-width: 110px; font-size:14px; box-shadow:none !important;
  }}
  #buttons-row button:hover {{ filter: brightness(1.08); }}
  #buttons-row button[disabled] {{ opacity:0.6; cursor:not-allowed; filter:none; }}
  #status {{ color: var(--muted); font-size: 14px; text-align:center; display:inline-block; white-space: nowrap; }}
  #transcript {{ 
    display:block;
    border:1px solid var(--border, #c8ccd5);
    border-radius:12px;
    padding:10px;
    height:clamp(295px, 40vh, 675px);
    overflow:auto;
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background:var(--panel-2, #f7f7fa);
    color: var(--text, #1f232b);
    max-width: 760px;
    margin: 10px auto 0;
    box-shadow: 0 1px 0 rgba(0,0,0,0.02), 0 0 0 1px rgba(0,0,0,0.02) inset;
  }}
  /* Below-transcript loading notifier */
  #notifier {{ 
    display:none; align-items:center; justify-content:center; gap:10px; 
    margin: 10px auto 0; padding:10px 14px; border:1px solid var(--border); border-radius:12px; 
    background: var(--panel-2); color: var(--text); max-width: 760px;
  }}
  #notifier .spin {{
    width:16px; height:16px; border:3px solid rgba(0,0,0,0.12); border-top-color: var(--acc); border-radius:50%;
    animation: alita-spin 0.8s linear infinite;
  }}
  #notifier .text {{ font-size: 13px; color: var(--muted); }}
  @keyframes alita-spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
  /* Toolbar below transcript */
  #toolbar {{
    display:flex; align-items:center; justify-content:center;
    gap: 10px; margin: 8px auto 0; max-width: 760px;
  }}
  #toolbar button {{
    -webkit-appearance:none; appearance:none; border:1px solid #1f232b !important; padding:8px 16px; border-radius:10px; font-weight:600; cursor:pointer;
    color:#fff !important; background:#2b2f36 !important; min-width: 96px; font-size:13px; box-shadow:none !important;
  }}
  #toolbar button:hover {{ filter: brightness(1.08); }}
  .msg {{ display:block; max-width: 100%; padding:8px 10px; border-radius:12px; margin:6px 0; line-height:1.45; white-space:pre-wrap; }}
  .u {{ background:#eceef2; color: var(--text); border:1px solid var(--border); }}
  .a {{ background:#f5f6f8; color: var(--text); border:1px solid var(--border); }}
  .role {{ display:block; font-size:11px; color: var(--muted); margin-bottom:4px; }}
</style>
<div id=outer>
  <div id=container>
  <div id=avatar-row>
    <img id=avatar src="{avatar_src}" alt="Alita Avatar" onerror="this.onerror=null; this.src='https://placehold.co/84x84/667eea/ffffff?text=A';" />
  </div>
  <div id=buttons-row>
    <button id=start>Start</button>
    <button id=stop disabled>Stop</button>
  </div>
  <div id=settings-row>
    <label for=provider style="font-size:13px;color:var(--muted);">Provider</label>
    <select id=provider title="Web search provider" style="padding:6px 10px;border-radius:10px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);">
      <option value="auto">Auto</option>
      <option value="tavily">Tavily</option>
      <option value="duckduckgo">DuckDuckGo</option>
    </select>
    <span id=status>Idle</span>
  </div>
  <div id=transcript title="Live transcript"></div>
  <div id=notifier>
    <div class="spin" aria-hidden="true"></div>
    <div id=notifier-text class="text">Working…</div>
  </div>
  <div id=toolbar>
    <button id=clearbtn title="Clear transcript and logs">Clear</button>
  </div>
  <details id=rawbox style="margin-top:10px;">
    <summary>Show raw events</summary>
    <pre id=rawlog style="background:var(--panel-2); border:1px solid var(--border); border-radius:10px; padding:8px; max-height:clamp(160px, 24vh, 360px); overflow:auto; color:var(--text);"></pre>
  </details>
  <audio id=remoteAudio autoplay playsinline></audio>
  <!-- Save reply toolbar below main container -->
  <div id=savebar style="display:flex;align-items:center;justify-content:center;gap:12px;margin-top:10px;">
    <label for=savereplyfmt style="font-size:13px;color:var(--muted);">Save reply</label>
    <select id=savereplyfmt title="Save last assistant reply format" style="padding:6px 10px;border-radius:10px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);">
      <option value="md">MD</option>
      <option value="pdf">PDF</option>
      <option value="docx">DOCX</option>
      <option value="txt">TXT</option>
      <option value="json">JSON</option>
      <option value="pptx">PPTX</option>
    </select>
    <input id=savereplyfn type=text placeholder="assistant-reply.ext" style="padding:6px 8px;border-radius:10px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);min-width:220px;" />
    <button id=savereplybtn>Save reply</button>
  </div>
  </div>
</div>

<script>
    const startBtn = document.getElementById('start');
    const stopBtn = document.getElementById('stop');
    const statusEl = document.getElementById('status');
    const transcriptEl = document.getElementById('transcript');
    const avatarEl = document.getElementById('avatar');
    const providerSel = document.getElementById('provider');
    try {{ if (providerSel) providerSel.value = '{provider_default}'; }} catch {{}}
    const saveReplyFmt = document.getElementById('savereplyfmt');
    const saveReplyFn = document.getElementById('savereplyfn');
    const saveReplyBtn = document.getElementById('savereplybtn');
    try {{
      if (saveReplyFn) {{
        const dt = new Date();
        const pad = (n) => String(n).padStart(2,'0');
        const stamp = `${{dt.getFullYear()}}${{pad(dt.getMonth()+1)}}${{pad(dt.getDate())}}-${{pad(dt.getHours())}}${{pad(dt.getMinutes())}}`;
        saveReplyFn.value = `assistant-reply-${{stamp}}.md`;
      }}
    }} catch {{}}
    let recognition;
    let isListening = false;
    let isProcessing = false;
    let speechSynthesis = window.speechSynthesis;
    const rawLogEl = document.getElementById('rawlog');
    let toolBuf = '';
    // Notifier helpers
    const notifierEl = document.getElementById('notifier');
    const notifierText = document.getElementById('notifier-text');
    const clearBtn = document.getElementById('clearbtn');
    if (!window.__loadingReasons) window.__loadingReasons = new Map();
    function updateNotifier() {{
      try {{
        const reasons = window.__loadingReasons;
        if (reasons && reasons.size > 0) {{
          // Show the last inserted reason's message
          let msg = 'Working…';
          for (const v of reasons.values()) msg = v || msg;
          if (notifierText) notifierText.textContent = msg;
          if (notifierEl) notifierEl.style.display = 'flex';
        }} else {{
          if (notifierEl) notifierEl.style.display = 'none';
        }}
      }} catch (_) {{}}
    }}
    function setLoading(reason, message) {{
      try {{ window.__loadingReasons.set(String(reason), String(message || 'Working…')); updateNotifier(); }} catch(_ ){{}}
    }}
    function clearLoading(reason) {{
      try {{ window.__loadingReasons.delete(String(reason)); updateNotifier(); }} catch(_){{}}
    }}
    try {{
      if (clearBtn) clearBtn.onclick = () => {{
        try {{ transcriptEl.innerHTML = ''; }} catch {{}}
        try {{ lastDiv = null; lastRole = null; }} catch {{}}
        try {{ if (rawLogEl) rawLogEl.textContent = ''; }} catch {{}}
        try {{ window.__lastAssistantText = ''; }} catch {{}}
        try {{ if (window.__loadingReasons) window.__loadingReasons.clear(); }} catch {{}}
        try {{ if (window.__recentTools) window.__recentTools.clear(); }} catch {{}}
        try {{ if (window.__inFlightTools) window.__inFlightTools.clear(); }} catch {{}}
        try {{ if (notifierEl) notifierEl.style.display = 'none'; }} catch {{}}
      }};
    }} catch {{}}

  function logRaw(obj, label='event') {{
    try {{
      if (!rawLogEl) return;
      const time = new Date().toISOString().split('T')[1].replace('Z','');
      const line = `[${{time}}] ${{label}}: ` + (typeof obj === 'string' ? obj : JSON.stringify(obj));
      rawLogEl.textContent += (rawLogEl.textContent ? "\n" : "") + line;
      if (rawLogEl.textContent.length > 80000) {{
        rawLogEl.textContent = rawLogEl.textContent.slice(-60000);
      }}
      rawLogEl.scrollTop = rawLogEl.scrollHeight;
    }} catch (_) {{}}
  }}

  let lastRole = null; let lastDiv = null;

// Initialize speech recognition
function initSpeechRecognition() {{
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
        appendLine('system', 'Speech recognition not supported in this browser.');
        return false;
    }}
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {{
        isListening = true;
        statusEl.textContent = 'Listening...';
        avatarEl.classList.add('listening');
        startBtn.disabled = true;
        stopBtn.disabled = false;
    }};
    
    recognition.onresult = (event) => {{
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {{
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {{
                finalTranscript += transcript;
            }} else {{
                interimTranscript += transcript;
            }}
        }}
        
        if (finalTranscript) {{
            appendLine('user', finalTranscript);
            processWithOllama(finalTranscript).catch(console.error);
        }}
    }};
    
    recognition.onerror = (event) => {{
        console.error('Speech recognition error:', event.error);
        statusEl.textContent = 'Error: ' + event.error;
    }};
    
    recognition.onend = () => {{
        if (isListening && !isProcessing) {{
            // Restart recognition if we're still supposed to be listening
            setTimeout(() => recognition.start(), 100);
        }}
    }};
    
    return true;
}}

// Process with Ollama (real API call with tool calling)
async function processWithOllama(text) {{
    if (isProcessing) return;
    
    isProcessing = true;
    statusEl.textContent = 'Processing...';
    avatarEl.classList.remove('listening');
    avatarEl.classList.add('speaking');
    setLoading('ollama', 'Processing with Ollama...');
    
    try {{
        // Check for tool calls first (similar to OpenAI Live Assistant)
        if (tryHandleTool(text)) {{
            return; // Tool handling will manage the response
        }}
        
        // Make actual API call to Ollama
        const response = await fetch('http://localhost:11434/api/generate', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                model: '{ai_model}',
                prompt: text,
                stream: false,
                system: "You are AlitaOS, a helpful assistant. Provide clear, concise responses suitable for voice conversation. Keep responses under 100 words when possible. If asked about current information like time, weather, news, or stock prices, suggest using search tools."
            }})
        }});
        
        if (!response.ok) {{
            throw new Error(`HTTP error! status: ${{response.status}}`);
        }}
        
        const data = await response.json();
        const assistantResponse = data.response || 'Sorry, I could not process your request.';
        
        appendLine('assistant', assistantResponse);
        speakText(assistantResponse);
        
        // Store for save functionality
        try {{ window.__lastAssistantText = assistantResponse; }} catch {{}}
        
    }} catch (error) {{
        console.error('Error calling Ollama API:', error);
        const errorMsg = 'Sorry, I could not connect to Ollama. Please make sure Ollama is running locally.';
        appendLine('assistant', errorMsg);
        speakText(errorMsg);
    }} finally {{
        isProcessing = false;
        avatarEl.classList.remove('speaking');
        clearLoading('ollama');
        if (isListening) {{
            statusEl.textContent = 'Listening...';
            avatarEl.classList.add('listening');
        }} else {{
            statusEl.textContent = 'Idle';
        }}
    }}
}}

  // Tool protocol within the embedded UI (copied from OpenAI Live Assistant)
  function tryHandleTool(data) {{
    // Deduplication store for recent tool invocations (name+args) within a short window
    if (!window.__recentTools) window.__recentTools = new Map();
    if (!window.__inFlightTools) window.__inFlightTools = new Set();
    // Track handled response_ids to avoid multiple tools per assistant turn
    if (!window.__handledResponseIds) window.__handledResponseIds = new Map();
    const recentTools = window.__recentTools;
    const handledByResp = window.__handledResponseIds;
    
    function detectAndRunFromText(txt) {{
      if (!txt || typeof txt !== 'string') return false;
      // search("...") or search('...')
      let m = txt.match(/\\bsearch\\((["'`])([\\s\\S]*?)\\1\\)/);
      if (m && m[2]) {{
        return runAndRender({{ name: 'search.web', args: {{ query: m[2], max_results: 6 }} }});
      }}
      // natural language search intent like: search for ...
      m = txt.match(/\\bsearch\\s+for\\s+([^\\.;\\n]+)[\\.;\\n]?/i);
      if (m && m[1]) {{
        return runAndRender({{ name: 'search.web', args: {{ query: m[1].trim(), max_results: 6 }} }});
      }}
      // direct time intent patterns (trigger web search tool which has time resolver)
      const t = txt.match(/\\b(?:what\\s+time\\s+is\\s+it\\s+in|current\\s+time\\s+in|local\\s+time\\s+in|time\\s+in)\\s+([A-Za-z ,\\-]+)\\b/i);
      if (t && t[1]) {{
        return runAndRender({{ name: 'search.web', args: {{ query: ('current time in ' + t[1]).trim(), max_results: 3 }} }});
      }}
      // Generic current-info heuristic: if the assistant text suggests current/real-time info topics, trigger a web search
      try {{
        const hasCurrent = /\\b(latest|current|today|breaking|now|as of now|recent)\\b/i.test(txt);
        const hasTopic = /\\b(news|price|prices|time|weather|status|score|scores|update|updates|market)\\b/i.test(txt);
        if (hasCurrent && hasTopic) {{
          return runAndRender({{ name: 'search.web', args: {{ query: txt.slice(0, 200), max_results: 6 }} }});
        }}
      }} catch {{}}
      return false;
    }}
    
    return detectAndRunFromText(data);
  }}
  
  // Execute tools and render results
  async function runAndRender(tool) {{
    try {{
      setLoading('tool', `Running ${{tool.name}}...`);
      const response = await fetch('/tool_exec', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(tool)
      }});
      
      if (response.ok) {{
        const result = await response.json();
        if (result.content) {{
          appendLine('assistant', result.content);
          speakText(result.content);
        }}
      }}
    }} catch (error) {{
      console.error('Tool execution error:', error);
    }} finally {{
      clearLoading('tool');
    }}
    return true;
  }}

  function appendLine(role, text) {{
    if (!text) return;
    if (lastDiv && lastRole === role) {{
      lastDiv.textContent += text;
      try {{ if (role === 'assistant') {{ if (!window.__lastAssistantText) window.__lastAssistantText = ''; window.__lastAssistantText += text; }} }} catch {{}}
    }} else {{
      const div = document.createElement('div');
      div.className = 'msg ' + (role === 'assistant' ? 'a' : 'u');
      const label = document.createElement('span');
      label.className = 'role';
      label.textContent = (role === 'assistant' ? 'Alita' : 'You');
      div.appendChild(label);
      const span = document.createElement('span');
      span.textContent = text;
      div.appendChild(span);
      transcriptEl.appendChild(div);
      lastDiv = span;
      lastRole = role;
      try {{ if (role === 'assistant') window.__lastAssistantText = text; }} catch {{}}
    }}
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }}

// Text-to-speech
function speakText(text) {{
    if (!speechSynthesis) return;
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.8;
    
    const voices = speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
        voice.name.includes('Natural') || 
        voice.name.includes('Enhanced') ||
        voice.name.includes('Premium')
    ) || voices.find(voice => voice.lang.startsWith('en'));
    
    if (preferredVoice) {{
        utterance.voice = preferredVoice;
    }}
    
    speechSynthesis.speak(utterance);
}}

// Event listeners
startBtn.onclick = () => {{
    if (initSpeechRecognition()) {{
        recognition.start();
    }}
}};

stopBtn.onclick = () => {{
    isListening = false;
    if (recognition) {{
        recognition.stop();
    }}
    statusEl.textContent = 'Idle';
    avatarEl.classList.remove('listening', 'speaking');
    startBtn.disabled = false;
    stopBtn.disabled = true;
}};

// Initialize voices when they're loaded
speechSynthesis.onvoiceschanged = () => {{
    // Voices are now loaded
}};
</script>
        """,
        height=650,
    )

