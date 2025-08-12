  #!/usr/bin/env python3
"""
AlitaOS - Streamlit Version
A streamlined AI assistant powered by OpenAI
"""

import streamlit as st
import os
import sys
from pathlib import Path
import base64
import io
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import tempfile
import subprocess
from typing import Optional, List
import time
import wave

# OpenAI client for transcription
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # Will handle gracefully at runtime

# Add the app directory to Python path for imports
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import our tools
try:
    from tools.image import generate_image
    from tools.search import search_information
    from tools.stock import get_stock_price
    from tools.chart import create_chart
    from tools.python_file import create_python_file, execute_python_code
    from utils.ai_models import get_llm
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure you're running from the correct directory with dependencies installed")
    st.stop()

# Components for embedding custom HTML/JS (for OpenAI Realtime WebRTC UI)
from streamlit.components.v1 import html as st_html

# Load environment variables
from dotenv import load_dotenv, find_dotenv
try:
    load_dotenv(find_dotenv())
except Exception:
    # Fallback to local directory if find_dotenv fails
    load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AlitaOS",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Global light theme CSS
st.markdown("""
<style>
  :root {
    --bg:#ffffff; --panel:#f7f7f9; --panel-2:#f2f3f5; --border:#e6e8ec; --muted:#6b7280; --text:#1f2937; 
    --charcoal:#2b2f36; --acc:#6f7dff; --acc2:#9b5cff;
  }

  html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important; color: var(--text);
  }
  /* Simple centered title with charcoal underline */
  .main-header {
    text-align: center; margin: 8px 0 24px 0; color: var(--charcoal);
  }
  .main-header h1 { font-weight: 700; letter-spacing: 0.2px; margin: 0; }
  .main-header .underline { width: 120px; height: 2px; background: var(--charcoal); margin: 10px auto 0 auto; border-radius: 2px; }
  .top-nav { text-align:center; margin: 6px 0 16px 0; color: var(--muted); }
  .top-nav a { color: var(--charcoal); text-decoration: none; margin: 0 10px; font-size: 13px; }
  .top-nav a:hover { text-decoration: underline; }

  /* Utility muted boxes */
  .tool-card { background: var(--panel); padding: 0.75rem; border-radius: 10px; border:1px solid var(--border); margin: 0.75rem 0; }
  .success-message { background: #eefbf1; color: #185a2b; padding: 1rem; border-radius: 10px; border:1px solid #d6f5de; }
  .error-message { background: #fff1f1; color: #7a1a1a; padding: 1rem; border-radius: 10px; border:1px solid #ffd6d6; }

  /* Hide Streamlit black top bar and sidebar for a clean canvas */
  [data-testid="stHeader"], header[tabindex="0"], .stDeployButton { display: none !important; }
  [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }
  /* Centered main container with max width */
  [data-testid="stAppViewContainer"] > .main {
    max-width: 1300px;
    margin-left: auto; margin-right: auto;
    padding-left: 1rem; padding-right: 1rem;
  }
  /* Keep a soft panel style where we previously themed sidebar, for consistency if re-enabled */
  [data-testid="stSidebar"] > div:first-child { background: var(--panel); border-right: 1px solid var(--border); }
  [data-testid="stSidebar"] * { color: var(--text); }

  /* Inputs, selects, textareas */
  input[type="text"], input[type="search"], input[type="number"], textarea, select,
  div[role="combobox"], .stDateInput input, .stTimeInput input {
    background: var(--panel-2) !important; border:1px solid var(--border) !important; color: var(--text) !important;
    border-radius: 10px !important;
  }
  /* Buttons (Streamlit) keep default; our custom buttons use gradient */
  #controls button { background: linear-gradient(90deg, var(--acc) 0%, var(--acc2) 100%) !important; color:#fff !important; }
  #controls button:hover { filter: brightness(0.98); }

  /* Expanders */
  details > summary { background: var(--panel) !important; border:1px solid var(--border) !important; border-radius: 10px !important; color: var(--text) !important; }
  details[open] > summary { border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important; }
  details > div[role="region"] { background: var(--panel) !important; border:1px solid var(--border) !important; border-top: none !important; border-bottom-left-radius: 10px !important; border-bottom-right-radius: 10px !important; }

  /* Tables and dataframes */
  .stDataFrame, .stTable { background: var(--panel); border:1px solid var(--border); border-radius: 10px; }

  /* Code blocks */
  pre, code, .stMarkdown pre, .stCode > div { background: var(--panel-2) !important; color: var(--text) !important; border:1px solid var(--border); border-radius: 10px; }

  /* Headers */
  h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2 { color: var(--charcoal) !important; }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'llm' not in st.session_state:
        try:
            st.session_state.llm = get_llm()
        except Exception as e:
            st.error(f"Failed to initialize OpenAI client: {e}")
            st.error("Please check your OPENAI_API_KEY in the .env file")
            st.stop()

def transcribe_audio_bytes(audio_data: bytes, mime_type: Optional[str] = None) -> Optional[str]:
    """Transcribe raw audio bytes using OpenAI Whisper API.

    Args:
        audio_data: Raw audio bytes (e.g., WAV from st.audio_input)
        mime_type: Reported MIME type (e.g., 'audio/wav')

    Returns:
        The transcribed text if successful, otherwise None.
    """
    if not audio_data:
        return None
    if OpenAI is None:
        st.error("openai package not available. Please install the official OpenAI Python SDK.")
        return None
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not set. Add it to your .env or environment.")
        return None

    # Determine file extension from MIME for better compatibility
    ext = "wav"
    if mime_type:
        if "mpeg" in mime_type:
            ext = "mp3"
        elif "mp4" in mime_type or "mp4a" in mime_type:
            ext = "m4a"
        elif "ogg" in mime_type:
            ext = "ogg"
        elif "webm" in mime_type:
            ext = "webm"
        elif "wav" in mime_type:
            ext = "wav"

    try:
        client = OpenAI()
        # Write bytes to a temp file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=(f"audio.{ext}", f, f"audio/{ext}")
            )

        # Clean up temp file
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        # Depending on SDK version, transcript may be an object or dict-like
        if hasattr(transcript, "text"):
            return transcript.text
        if isinstance(transcript, dict) and "text" in transcript:
            return transcript["text"]
        return None
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None

def display_header():
    """Display the main header"""
    # Global layout overrides: center Streamlit main container and remove side paddings
    st.markdown(
        """
        <style>
        section.main > div.block-container {
          max-width: 1200px;
          margin: 0 auto !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
        }
        [data-testid="stAppViewContainer"] > .main {
          display: flex;
          justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div class="main-header">
      <h1>AlitaOS</h1>
      <div class="underline"></div>
    </div>
    <div class="top-nav">
      <a href="?tab=live">Live Assistant</a>
      <span>•</span>
      <a href="?tab=chat">Chat</a>
      <span>•</span>
      <a href="?tab=images">Images</a>
      <span>•</span>
      <a href="?tab=search">Search</a>
      <span>•</span>
      <a href="?tab=stocks">Stocks</a>
      <span>•</span>
      <a href="?tab=charts">Charts</a>
      <span>•</span>
      <a href="?tab=python">Python</a>
    </div>
    """, unsafe_allow_html=True)

def get_selected_tool() -> str:
    """Read the selected tool from query params (top nav links)."""
    mapping = {
        "live": "🎧 Live Assistant",
        "chat": "💬 Chat Assistant",
        "images": "🖼️ Image Generation",
        "search": "🔍 Information Search",
        "stocks": "📈 Stock Prices",
        "charts": "📊 Data Visualization",
        "python": "🐍 Python Code",
    }
    default_key = "live"
    try:
        qp = st.query_params
        tab = qp.get("tab")
        if isinstance(tab, list):
            tab = tab[0] if tab else None
        tab = tab or default_key
    except Exception:
        tab = default_key
    return mapping.get(tab, mapping[default_key])

def handle_chat_assistant():
    """Handle the chat assistant functionality"""
    st.subheader("💬 Chat with AlitaOS")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input (also handle voice-provided prompt on rerun)
    voice_prompt = st.session_state.pop("__voice_prompt", None) if "__voice_prompt" in st.session_state else None
    user_input = st.chat_input("Ask me anything...")
    prompt = voice_prompt or user_input
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.llm.invoke(prompt)
                    response_text = response.content if hasattr(response, 'content') else str(response)
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def handle_live_assistant():
    """True OpenAI Realtime 'live' API via WebRTC (browser <-> OpenAI) with local proxy."""
    # Centered header + caption
    st.markdown(
        """
        <div style="text-align:center;margin-bottom:8px;">
          <h2 style="margin:0;">🎧 Live Assistant</h2>
          <div style="color:var(--muted);font-size:14px;">Click Start to grant mic access. Bi-directional low-latency voice.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Proxy endpoint (no UI). Defaults to http(s)://localhost:8787
    proxy_url_default = f"http{'s' if os.getenv('STREAMLIT_SERVER_ENABLE_CORS','false').lower()=='true' else ''}://localhost:" + os.getenv("ALITA_REALTIME_PORT", "8787")
    proxy_url = os.getenv("ALITA_REALTIME_URL", proxy_url_default)

    # Load avatar image from common locations and formats, prefer app/static/alita.*
    avatar_src = "https://placehold.co/144x144?text=Alita"
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

    # Provide Start/Stop UI with transcript and animated avatar (centered via Streamlit columns)
    left_col, mid_col, right_col = st.columns([1, 8, 1], gap="small")
    with mid_col:
        st_html(
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
  #alita-wrap {{ display:flex; align-items:center; gap:16px; margin-bottom:14px; }}
  #avatar {{ width:84px; height:84px; border-radius:50%; object-fit:cover; box-shadow:0 0 0px rgba(111,125,255,0.0); transition: box-shadow 160ms ease; border:2px solid var(--border); background:#ddd; display:block; flex:0 0 auto; }}
  #avatar.speaking {{ box-shadow:0 0 22px rgba(111,125,255,0.55); }}
  #alita-wrap {{ display:flex; align-items:center; justify-content:center; gap:18px; margin: 0 auto 14px; width: fit-content; max-width: 100%; box-sizing:border-box; position: static; left: auto; transform: none; overflow: visible; margin-left: 120px; }}
  #controls {{ display:flex; align-items:center; justify-content:center; gap:16px; }}
  #controls button {{
    -webkit-appearance:none; appearance:none; border:1px solid #1f232b !important; padding:10px 20px; border-radius:12px; font-weight:600; cursor:pointer;
    color:#fff !important; background:#2b2f36 !important; min-width: 110px; font-size:14px; box-shadow:none !important;
  }}
  /* specific button rules can go here if needed */
  #controls button:hover {{ filter: brightness(1.08); }}
  #controls button[disabled] {{ opacity:0.6; cursor:not-allowed; filter:none; }}
  #status {{ margin-left:12px; color: var(--muted); font-size: 14px; min-width: 200px; text-align:left; display:inline-block; white-space: nowrap; }}
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
  .msg {{ display:block; max-width: 100%; padding:8px 10px; border-radius:12px; margin:6px 0; line-height:1.45; white-space:pre-wrap; }}
  .u {{ background:#eceef2; color: var(--text); border:1px solid var(--border); }}
  .a {{ background:#f5f6f8; color: var(--text); border:1px solid var(--border); }}
  .role {{ display:block; font-size:11px; color: var(--muted); margin-bottom:4px; }}
</style>
<div id=outer>
  <div id=container>
  <div id=alita-wrap>
    <img id=avatar src="{avatar_src}" alt="Alita Avatar" onerror="this.onerror=null; this.src='https://placehold.co/84x84?text=Alita';" />
    <div id=controls>
      <button id=start>Start</button>
      <button id=stop disabled>Stop</button>
      <label for=provider style="margin-left:12px;font-size:13px;color:var(--muted);">Provider</label>
      <select id=provider title="Web search provider" style="padding:6px 10px;border-radius:10px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);">
        <option value="auto">Auto</option>
        <option value="tavily">Tavily</option>
        <option value="duckduckgo">DuckDuckGo</option>
      </select>
      <span id=status>Idle</span>
    </div>
  </div>
  <div id=transcript title="Live transcript"></div>
  <details id=rawbox style="margin-top:10px;">
    <summary>Show raw events</summary>
    <pre id=rawlog style="background:var(--panel-2); border:1px solid var(--border); border-radius:10px; padding:8px; max-height:clamp(160px, 24vh, 360px); overflow:auto; color:var(--text);"></pre>
  </details>
  <audio id=remoteAudio autoplay playsinline></audio>
  </div>
</div>
<script>
    const startBtn = document.getElementById('start');
    const stopBtn = document.getElementById('stop');
    const statusEl = document.getElementById('status');
    const remoteAudio = document.getElementById('remoteAudio');
    const transcriptEl = document.getElementById('transcript');
    const avatarEl = document.getElementById('avatar');
    const providerSel = document.getElementById('provider');
    try {{ if (providerSel) providerSel.value = '{provider_default}'; }} catch {{}}
    let pc, micStream;
    let dc; // data channel
    let analyser, audioCtx, raf;
    const rawLogEl = document.getElementById('rawlog');
    let toolBuf = '';

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
  // Extract human-readable text from Realtime API events
  function extractTextFromEvent(evt) {{
    try {{
      if (!evt) return '';
      // Streaming deltas (support both string and object shapes)
      if (evt.type && evt.type.endsWith('.delta')) {{
        if (typeof evt.delta === 'string') return evt.delta;
        if (evt.delta && typeof evt.delta.text === 'string') return evt.delta.text;
      }}
      // Unified response format
      if (evt.type === 'response.completed' && evt.response && Array.isArray(evt.response.output)) {{
        let out = '';
        for (const part of evt.response.output) {{
          if (!part || !Array.isArray(part.content)) continue;
          for (const c of part.content) {{
            if ((c.type === 'output_text' || c.type === 'text') && typeof c.text === 'string') {{
              out += c.text;
            }}
          }}
        }}
        return out;
      }}
      // Some SDKs send message items directly
      if (Array.isArray(evt.items)) {{
        let out = '';
        for (const it of evt.items) {{
          if (!it || !Array.isArray(it.content)) continue;
          for (const c of it.content) {{
            if ((c.type === 'output_text' || c.type === 'text') && typeof c.text === 'string') out += c.text;
          }}
        }}
        return out;
      }}
      // Fallback
      if (typeof evt.text === 'string') return evt.text;
    }} catch (_) {{}}
    return '';
  }}

  function appendLine(role, text) {{
    if (!text) return;
    if (lastDiv && lastRole === role) {{
      lastDiv.textContent += text;
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
    }}
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }}

  // Tool protocol within the embedded UI
  function tryHandleTool(data) {{
    // Deduplication store for recent tool invocations (name+args) within a short window
    if (!window.__recentTools) window.__recentTools = new Map();
    if (!window.__inFlightTools) window.__inFlightTools = new Set();
    // Track handled response_ids to avoid multiple tools per assistant turn
    if (!window.__handledResponseIds) window.__handledResponseIds = new Map();
    const recentTools = window.__recentTools;
    const handledByResp = window.__handledResponseIds;
    function getResponseId(d) {{
      try {{
        if (!d) return null;
        if (typeof d.response_id === 'string') return d.response_id;
        if (d.response && typeof d.response.id === 'string') return d.response.id;
        if (typeof d.id === 'string' && (d.type === 'response.created' || d.type === 'response.done')) return d.id;
      }} catch {{}}
      return null;
    }}
    function detectAndRunFromText(txt) {{
      if (!txt || typeof txt !== 'string') return false;
      // search("...") or search('...')
      let m = txt.match(/\bsearch\((["'`])([\s\S]*?)\1\)/);
      if (m && m[2]) {{
        return runAndRender({{ name: 'search.web', args: {{ query: m[2], max_results: 6 }} }});
      }}
      // natural language search intent like: search for ...
      m = txt.match(/\bsearch\s+for\s+([^\.;\n]+)[\.;\n]?/i);
      if (m && m[1]) {{
        return runAndRender({{ name: 'search.web', args: {{ query: m[1].trim(), max_results: 6 }} }});
      }}
      // direct time intent patterns (trigger web search tool which has time resolver)
      const t = txt.match(/\b(?:what\s+time\s+is\s+it\s+in|current\s+time\s+in|local\s+time\s+in|time\s+in)\s+([A-Za-z ,\-]+)\b/i);
      if (t && t[1]) {{
        return runAndRender({{ name: 'search.web', args: {{ query: ('current time in ' + t[1]).trim(), max_results: 3 }} }});
      }}
      // JSON search payload in a text string, e.g. {{"query":"..."}}
      try {{
        if (/\\{{/.test(txt) && /\"query\"\s*:/.test(txt)) {{
          let j = JSON.parse(txt);
          const tool = normalizeTool(j, txt);
          if (tool) return runAndRender(tool);
        }}
      }} catch {{}}
      // Generic current-info heuristic: if the assistant text suggests current/real-time info topics, trigger a web search
      try {{
        const hasCurrent = /\b(latest|current|today|breaking|now|as of now|recent)\b/i.test(txt);
        const hasTopic = /\b(news|price|prices|time|weather|status|score|scores|update|updates|market)\b/i.test(txt);
        if (hasCurrent && hasTopic) {{
          return runAndRender({{ name: 'search.web', args: {{ query: txt.slice(0, 200), max_results: 6 }} }});
        }}
      }} catch {{}}
      // "generate an image of ..." heuristic
      const im = txt.match(/\b(?:generate\s+(?:an\s+)?image\s+of|image\s+of)\s+([^\.\n]+)(?:[\.|\n]|$)/i);
      if (im && im[1]) {{
        let prompt = im[1].trim();
        let style = null;
        const lower = txt.toLowerCase();
        if (lower.includes('photorealistic')) style = 'photorealistic';
        else if (lower.includes('watercolor')) style = 'watercolor';
        else if (lower.includes('3d')) style = '3d';
        else if (lower.includes('anime')) style = 'anime';
        else if (lower.includes('cartoon')) style = 'cartoon';
        else if (lower.includes('line art')) style = 'line-art';
        else if (lower.includes('oil painting')) style = 'oil-painting';
        return runAndRender({{ name: 'image.generate', args: {{ prompt, size: '1024x1024', ...(style ? {{style}} : {{}}) }} }});
      }}
      return false;
    }}
    // Helper: collect JSON candidates from a string using brace balance
    function scanCandidates(str) {{
      const list = [];
      let depth = 0, startIdx = -1;
      for (let i = 0; i < str.length; i++) {{
        const ch = str[i];
        if (ch === '{{') {{
          if (depth === 0) startIdx = i;
          depth++;
        }} else if (ch === '}}') {{
          if (depth > 0) depth--;
          if (depth === 0 && startIdx !== -1) {{
            list.push(str.slice(startIdx, i + 1));
            startIdx = -1;
          }}
        }}
      }}
      return list;
    }}

    // Streamed text delta handling: only buffer if it looks like JSON; otherwise let text render
    try {{
      if (typeof data === 'object' && data.type && typeof data.type === 'string' && data.type.endsWith('.delta') && typeof data.delta === 'string') {{
        const delta = data.delta;
        // If we are already buffering (inside a JSON object) OR this delta introduces an opening brace, keep buffering
        if (toolBuf.length > 0 || delta.indexOf('{{') !== -1) {{
          toolBuf += delta;
          // If we haven't seen an opening brace yet, do not suppress normal text
          if (toolBuf.indexOf('{{') === -1) return false;
          // If we have an opening brace, suppress echo until we finish scanning
          if (toolBuf.indexOf('}}') !== -1) {{
            const candidates = scanCandidates(toolBuf);
            toolBuf = '';
            for (const c of candidates) {{
              try {{
                let j = JSON.parse(c);
                if (typeof j === 'string') {{ try {{ j = JSON.parse(j); }} catch {{}} }}
                const tool = normalizeTool(j, c);
                if (tool) return runAndRender(tool);
              }} catch {{}}
            }}
            // Suppress echo if we saw JSON-like content even if no tool matched
            if (candidates.length > 0) return true;
          }}
          return true; // actively buffering JSON-like content
        }}
        // Not JSON-like: allow normal text rendering
        return false;
      }}
    }} catch {{}}

    // Normalize possible tool signal to {{name, args}}
    function normalizeTool(obj, rawStr) {{
      if (!obj) return null;
      if (obj.tool && typeof obj.tool === 'object') return {{ name: obj.tool.name, args: obj.tool.args || {{}} }};
      if (obj.name && typeof obj.name === 'string') return {{ name: obj.name, args: obj.args || {{}} }};
      // Explicit search schema
      if (obj.function === 'search' || obj.function === 'web_search') {{
        const q = (obj.arguments && (obj.arguments.query || obj.arguments.q)) || null;
        const provider = obj.arguments && obj.arguments.provider;
        if (q) return {{ name: 'search.web', args: {{ query: q, ...(provider ? {{provider}} : {{}}) }} }};
      }}
      // Action schemas from some assistants, e.g., action: check_current_world_leader, country: Russia
      if (typeof obj.action === 'string') {{
        const act = obj.action.toLowerCase();
        if (act.includes('world_leader') || act.includes('current_leader') || act.includes('current_world_leader')) {{
          const country = obj.country || obj.region || obj.target || '';
          const q = country ? ('current leader of ' + country) : 'current world leaders';
          return {{ name: 'search.web', args: {{ query: q, max_results: 6 }} }};
        }}
      }}
      // Function-call schema: function 'generate_image' with an arguments object
      if (typeof obj.function === 'string' && obj.arguments) {{
        if (obj.function === 'generate_image') {{
          const a = obj.arguments || {{}};
          const prompt = a.prompt || a.description || '';
          let size = a.size || '1024x1024';
          if (typeof size === 'string') {{
            const s = size.toLowerCase();
            if (s === 'small') size = '512x512';
            else if (s === 'medium') size = '1024x1024';
            else if (s === 'large') size = '1792x1024';
          }}
          const style = a.style || a.image_style || null;
          if (prompt) return {{ name: 'image.generate', args: {{ prompt, size, ...(style ? {{style}} : {{}}) }} }};
        }}
      }}
      // Heuristic: plain JSON with description/prompt
      if (typeof obj === 'object') {{
        const prompt = (typeof obj.prompt === 'string' && obj.prompt) ? obj.prompt : (typeof obj.description === 'string' ? obj.description : null);
        if (prompt) {{
          // map friendly sizes
          let size = obj.size || '1024x1024';
          if (typeof size === 'string') {{
            const s = size.toLowerCase();
            if (s === 'small') size = '512x512';
            else if (s === 'medium') size = '1024x1024';
            else if (s === 'large') size = '1792x1024';
          }}
          const style = obj.style || null;
          return {{ name: 'image.generate', args: {{ prompt, size, ...(style ? {{style}} : {{}}) }} }};
        }}
        // Heuristic: simple search payload
        if (obj.query && typeof obj.query === 'string') {{
          const provider = obj.provider || null;
          return {{ name: 'search.web', args: {{ query: obj.query, max_results: obj.max_results || 6, ...(provider ? {{provider}} : {{}}) }} }};
        }}
        // Heuristic: prompt-only object implies image request
        if (typeof obj.prompt === 'string' && !obj.query) {{
          let size = obj.size || '1024x1024';
          if (typeof size === 'string') {{
            const s = size.toLowerCase();
            if (s === 'small') size = '512x512';
            else if (s === 'medium') size = '1024x1024';
            else if (s === 'large') size = '1792x1024';
          }}
          const style = obj.style || null;
          return {{ name: 'image.generate', args: {{ prompt: obj.prompt, size, ...(style ? {{style}} : {{}}) }} }};
        }}
        // Some models emit an input object with description and size
        if (obj.input && (obj.input.prompt || obj.input.description)) {{
          const p = obj.input.prompt || obj.input.description;
          let size = obj.input.size || '1024x1024';
          if (typeof size === 'string') {{
            const s = size.toLowerCase();
            if (s === 'small') size = '512x512';
            else if (s === 'medium') size = '1024x1024';
            else if (s === 'large') size = '1792x1024';
          }}
          const style = obj.input.style || null;
          return {{ name: 'image.generate', args: {{ prompt: p, size, ...(style ? {{style}} : {{}}) }} }};
        }}
      }}
      // Heuristic: raw string mentions prompt/description JSON
      if (typeof rawStr === 'string' && (/\"prompt\"\s*:\s*\"/.test(rawStr) || /\"description\"\s*:\s*\"/.test(rawStr) || /\"query\"\s*:\s*\"/.test(rawStr))) {{
        try {{ const j = JSON.parse(rawStr); return normalizeTool(j); }} catch {{}}
      }}
      return null;
    }}

    // Try direct object
    try {{
      if (typeof data === 'object') {{
        // Ignore benign control pings like timezone settings
        if (data && typeof data.timezone === 'string') return true;
        // Detect from completed events only (avoid duplicate triggers on deltas)
        if (data && typeof data.type === 'string') {{
          // Mark this event as the last one so runAndRender can tag this response_id as handled
          try {{ window.__lastEvent = data; }} catch {{}}
          try {{ console.debug('[alita][tool] event type:', data.type, 'response_id:', getResponseId(data)); }} catch {{}}
          const rid = getResponseId(data);
          if (rid && handledByResp.has(rid)) return true;
          if (data.type === 'response.text.done' && typeof data.text === 'string') {{
            try {{ console.debug('[alita][tool] text.done:', data.text); }} catch {{}}
            if (detectAndRunFromText(data.text)) {{ try {{ console.debug('[alita][tool] detectAndRunFromText returned true (text.done)'); }} catch {{}}; return true; }}
            // Fallback: parse JSON text directly for tool payloads
            try {{
              if (/\"query\"\s*:/.test(data.text)) {{
                try {{ console.debug('[alita][tool] attempting JSON.parse on text.done'); }} catch {{}}
                let j = JSON.parse(data.text);
                const tool = normalizeTool(j, data.text);
                if (tool) {{ try {{ console.debug('[alita][tool] normalized tool from text.done:', tool); }} catch {{}}; return runAndRender(tool); }}
              }}
            }} catch {{}}
          }}
          if (data.type === 'response.audio_transcript.done' && typeof data.transcript === 'string') {{
            try {{ console.debug('[alita][tool] audio_transcript.done:', data.transcript); }} catch {{}}
            if (detectAndRunFromText(data.transcript)) {{ try {{ console.debug('[alita][tool] detectAndRunFromText returned true (audio)'); }} catch {{}}; return true; }}
            try {{
              const t = data.transcript;
              if (/\"query\"\s*:/.test(t) && /\\{{/.test(t)) {{
                try {{ console.debug('[alita][tool] attempting JSON.parse on audio transcript'); }} catch {{}}
                let j = JSON.parse(t);
                const tool = normalizeTool(j, t);
                if (tool) {{ try {{ console.debug('[alita][tool] normalized tool from audio transcript:', tool); }} catch {{}}; return runAndRender(tool); }}
              }}
            }} catch {{}}
          }}
          const tool = normalizeTool(data);
          if (tool) {{ try {{ console.debug('[alita][tool] normalized tool from direct object:', tool); }} catch {{}}; return runAndRender(tool); }}
        }}
      }}
    }} catch {{}}

    // Try string payloads: first detect textual tool intents, then extract JSON blocks
    if (typeof data === 'string') {{
      // If this is a serialized Realtime event (e.g., {{"type":"response.text.done", ...}}), ignore here
      try {{
        const maybe = JSON.parse(data);
        if (maybe && typeof maybe.type === 'string' && /^response\./.test(maybe.type)) return false;
      }} catch {{}}
      if (detectAndRunFromText(data)) return true;
      // Heuristic: if the assistant says they'll "generate an image of ...", infer an image.generate
      // Code fence case ```json ... ```
      const fenceMatch = data.match(/```json([\s\S]*?)```/i);
      const candidates = [];
      if (fenceMatch && fenceMatch[1]) {{ candidates.push(fenceMatch[1]); }}
      else {{
        // Brace-scan to collect all balanced JSON objects
        let depth = 0, startIdx = -1;
        for (let i = 0; i < data.length; i++) {{
          const ch = data[i];
          if (ch === '{{') {{
            if (depth === 0) startIdx = i;
            depth++;
          }} else if (ch === '}}') {{
            if (depth > 0) depth--;
            if (depth === 0 && startIdx !== -1) {{
              candidates.push(data.slice(startIdx, i + 1));
              startIdx = -1;
            }}
          }}
        }}
      }}
      let matchedTool = false;
      for (const c of candidates) {{
        try {{
          let j = JSON.parse(c);
          if (typeof j === 'string') {{
            try {{ j = JSON.parse(j); }} catch {{}}
          }}
          const tool = normalizeTool(j, c);
          if (tool) {{ matchedTool = true; return runAndRender(tool); }}
        }} catch {{}}
      }}
      // If no tool matched, allow normal handling so text deltas render
      if (matchedTool) return true;
    }}
    return false;
    function runAndRender(tool) {{
      try {{
        // Build a canonical, stable JSON string for args by sorting keys recursively
        function stableStringify(obj) {{
          if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
          if (Array.isArray(obj)) return '[' + obj.map(stableStringify).join(',') + ']';
          const keys = Object.keys(obj).sort();
          return '{{' + keys.map(k => JSON.stringify(k) + ':' + stableStringify(obj[k])).join(',') + '}}';
        }}
        const key = tool.name + '|' + stableStringify(tool.args || {{}});
        const now = Date.now();
        // 12s dedupe window
        if (recentTools.has(key) && now - recentTools.get(key) < 12000) {{ try {{ console.debug('[alita][tool] skip: within dedupe window for key', key); }} catch {{}}; return true; }}
        // Prevent re-entry while a same tool is currently in flight
        if (window.__inFlightTools.has(key)) {{ try {{ console.debug('[alita][tool] skip: in-flight key', key); }} catch {{}}; return true; }}
        recentTools.set(key, now);
        window.__inFlightTools.add(key);
        try {{ console.debug('[alita][tool] Running tool:', tool.name, 'with args:', tool.args, 'key:', key); }} catch {{}}
        try {{ logRaw('runTool ' + tool.name + ' ' + JSON.stringify(tool.args || {{}}), 'tool'); }} catch {{}}
        // Immediately cancel any ongoing assistant response to avoid fallback speech overlap
        try {{ cancelCurrentResponse(); }} catch {{}}
        // Mark the current response_id (if any) as handled to avoid a second tool from the same turn
        const rid = getResponseId(window.__lastEvent || {{}}) || null;
        if (rid) handledByResp.set(rid, now);
        appendLine('assistant', `Running tool: ${{tool.name}}...`);
      }} catch {{}}
      runTool(tool.name, tool.args).then(res => {{
        try {{ logRaw('tool result ' + (res && res.type ? res.type : 'unknown'), 'tool'); }} catch {{}}
        if (!res || !res.success) {{
          appendLine('assistant', (res && res.error) ? ('Tool error: ' + res.error) : 'Tool error');
          return;
        }}
        if (res.type === 'image' && res.data_url) return appendImage(res.data_url);
        if (res.type === 'time' && res.datetime_iso && res.tz) {{
          appendTime(res);
          try {{ cancelCurrentResponse(); requestSpokenTime(res); }} catch {{}}
          return;
        }}
        if (res.type === 'search' && Array.isArray(res.results)) {{
          appendSearch(res);
          try {{ requestSpokenAnswer(res); }} catch {{}}
          return;
        }}
        appendLine('assistant', 'Tool returned unsupported type.');
      }}).catch(err => appendLine('assistant', 'Tool error: ' + err))
        .finally(() => {{ try {{ window.__inFlightTools.delete(key); }} catch {{}} }});
      return true;
    }}
  }}

  async function runTool(name, args) {{
    const url = (function() {{
      try {{
        const base = new URL('{proxy_url}', window.location.origin);
        if (window.location.protocol === 'https:' && base.protocol !== 'https:') base.protocol = 'https:';
        return base.toString().replace(/\/$/, '') + '/tool';
      }} catch {{
        return (window.location.protocol === 'https:' ? 'https://' : 'http://') + 'localhost:8787/tool';
      }}
    }})();
    // Normalize queries for web search to reduce duplicates and noise
    try {{
      if (name === 'search.web' && args && typeof args.query === 'string') {{
        let q = args.query.trim();
        q = q.replace(/\b(right now|please|kindly|today)\b/gi, '').replace(/\s{2,}/g, ' ').trim();
        // Remove leading/trailing quotes/braces if the model emitted a JSON string as text
        if ((q.startsWith('{') && q.endsWith('}')) || (q.startsWith('"') && q.endsWith('"'))) {{
          try {{ const parsed = JSON.parse(q); if (parsed && typeof parsed.query === 'string') q = parsed.query; }} catch {{}}
        }}
        args.query = q;
        try {{ if (providerSel && providerSel.value && providerSel.value !== 'auto') args.provider = providerSel.value; }} catch {{}}
      }}
    }} catch {{}}
    const resp = await fetch(url, {{
      method: 'POST', headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify({{name, args}})
    }});
    return resp.json();
  }}

  function appendImage(dataUrl) {{
    const wrap = document.createElement('div');
    wrap.className = 'msg a';
    const label = document.createElement('span');
    label.className = 'role';
    label.textContent = 'Alita';
    wrap.appendChild(label);
    const img = document.createElement('img');
    img.src = dataUrl; img.alt = 'generated image';
    img.style.maxWidth = '100%'; img.style.borderRadius = '10px'; img.style.border = '1px solid var(--border)'; img.style.display='block';
    wrap.appendChild(img);
    transcriptEl.appendChild(wrap);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }}

  function appendSearch(res) {{
    const wrap = document.createElement('div');
    wrap.className = 'msg a';
    const label = document.createElement('span');
    label.className = 'role';
    label.textContent = 'Alita';
    wrap.appendChild(label);
    const meta = document.createElement('div');
    meta.style.fontSize = '12px'; meta.style.color = 'var(--muted)'; meta.style.marginTop = '2px';
    meta.textContent = 'Query: ' + (res.query || '') + (res.provider ? ('  |  Provider: ' + res.provider) : '');
    wrap.appendChild(meta);
    const list = document.createElement('div');
    list.style.display = 'grid';
    list.style.gap = '8px';
    list.style.marginTop = '6px';
    (res.results || []).forEach(function(r) {{
      const item = document.createElement('div');
      item.style.border = '1px solid var(--border)';
      item.style.borderRadius = '10px';
      item.style.padding = '10px';
      item.style.background = 'var(--panel-2)';
      const a = document.createElement('a');
      a.href = r.url; a.target = '_blank'; a.rel = 'noreferrer noopener';
      a.textContent = r.title || r.url;
      a.style.fontWeight = '600';
      a.style.color = 'var(--text)';
      const p = document.createElement('div');
      p.textContent = r.snippet || '';
      p.style.marginTop = '4px';
      item.appendChild(a);
      item.appendChild(p);
      list.appendChild(item);
    }});
    wrap.appendChild(list);
    transcriptEl.appendChild(wrap);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }}

  function requestSpokenAnswer(res) {{
    try {{
      if (!dc || dc.readyState !== 'open') return;
      var top = (res.results || []).slice(0, 3);
      var lines = [];
      for (var i = 0; i < top.length; i++) {{
        var r = top[i];
        var idx = (i + 1) + '. ';
        var line = idx + (r.title || '') + ' - ' + (r.url || '') + '\n' + ((r.snippet || '').slice(0, 220));
        lines.push(line);
      }}
      var instr = 'Using the following web results, answer the user\'s query succinctly and speak the answer. Cite sources inline as [1], [2].\n' +
                  'Query: ' + (res.query || '') + '\n' +
                  'Results:\n' + lines.join('\n');
      var payload = {{ type: 'response.create', response: {{ instructions: instr }} }};
      dc.send(JSON.stringify(payload));
    }} catch (e) {{}}
  }}

  function cancelCurrentResponse() {{
    try {{
      if (!dc || dc.readyState !== 'open') return;
      if (!window.__activeResponseId) return;
      dc.send(JSON.stringify({{ type: 'response.cancel' }}));
    }} catch {{}}
  }}

  function appendTime(res) {{
    const wrap = document.createElement('div');
    wrap.className = 'msg a';
    const label = document.createElement('span');
    label.className = 'role';
    label.textContent = 'Alita';
    wrap.appendChild(label);
    const box = document.createElement('div');
    box.style.border = '1px solid var(--border)';
    box.style.borderRadius = '10px';
    box.style.padding = '10px';
    box.style.background = 'var(--panel-2)';
    const title = document.createElement('div');
    title.style.fontWeight = '600';
    const place = res.place || '';
    const tz = res.tz || '';
    let human = res.datetime_iso || '';
    try {{
      const dt = new Date(res.datetime_iso);
      if (!isNaN(dt.getTime()) && tz) {{
        const fmt = new Intl.DateTimeFormat(undefined, {{ dateStyle: 'medium', timeStyle: 'long', timeZone: tz }});
        human = fmt.format(dt);
      }}
    }} catch {{}}
    title.textContent = `Local time in ${{place}} (${{tz}})`;
    const timeEl = document.createElement('div');
    timeEl.style.marginTop = '6px';
    timeEl.textContent = human + (res.utc_offset ? ` (UTC offset ${{res.utc_offset}})` : '');
    box.appendChild(title);
    box.appendChild(timeEl);
    if (res.source_url) {{
      const src = document.createElement('a');
      src.href = res.source_url; src.target = '_blank'; src.rel = 'noreferrer noopener';
      src.textContent = 'Source: worldtimeapi.org';
      src.style.display = 'inline-block';
      src.style.marginTop = '6px';
      box.appendChild(src);
    }}
    wrap.appendChild(box);
    transcriptEl.appendChild(wrap);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }}

  function requestSpokenTime(res) {{
    try {{
      if (!dc || dc.readyState !== 'open') return;
      const place = res.place || '';
      const tz = res.tz || '';
      let human = res.datetime_iso || '';
      try {{
        const dt = new Date(res.datetime_iso);
        if (!isNaN(dt.getTime()) && tz) {{
          const fmt = new Intl.DateTimeFormat('en-US', {{ dateStyle: 'full', timeStyle: 'long', timeZone: tz }});
          human = fmt.format(dt);
        }}
      }} catch {{}}
      const instr = `Speak the current local time clearly. Say: It is ${{human}} in ${{place}} (${{tz}}).`;
      const payload = {{ type: 'response.create', response: {{ instructions: instr }} }};
      dc.send(JSON.stringify(payload));
    }} catch {{}}
  }}

  async function start() {{
    startBtn.disabled = true; stopBtn.disabled = false; statusEl.textContent = 'Starting…';
    try {{
      // Preflight: check proxy /health before requesting mic
      const configuredPre = '{proxy_url}';
      function computeBase(urlStr) {{
        try {{
          const u = new URL(urlStr, window.location.origin);
          if (window.location.protocol === 'https:' && u.protocol !== 'https:') u.protocol = 'https:';
          return u.toString().replace(/\/$/, '');
        }} catch {{
          return (window.location.protocol === 'https:' ? 'https://' : 'http://') + 'localhost:8787';
        }}
      }}
      async function tryHealth(base) {{
        try {{ const r = await fetch(base + '/health', {{ method: 'GET' }}); return r && r.ok; }} catch {{ return false; }}
      }}
      let base = computeBase(configuredPre);
      let ok = await tryHealth(base);
      if (!ok) {{
        try {{ const u2 = new URL(base); u2.protocol = (u2.protocol === 'https:') ? 'http:' : 'https:'; base = u2.toString(); }} catch {{}}
        ok = await tryHealth(base.replace(/\/$/, ''));
      }}
      if (!ok) {{
        try {{ const u3 = new URL(base); u3.hostname = (u3.hostname === 'localhost') ? '127.0.0.1' : 'localhost'; base = u3.toString(); }} catch {{}}
        ok = await tryHealth(base.replace(/\/$/, ''));
      }}
      if (!ok) {{
        statusEl.textContent = 'Proxy unavailable on /health (is it running on :8787?)';
        logRaw('proxy health check failed for /health', 'error');
        startBtn.disabled = false; stopBtn.disabled = true; return;
      }}

      micStream = await navigator.mediaDevices.getUserMedia({{audio: true, video: false}});
      pc = new RTCPeerConnection({{iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}]}});
      micStream.getAudioTracks().forEach(t => pc.addTrack(t, micStream));
      pc.ontrack = (e) => {{
        const [stream] = e.streams;
        remoteAudio.srcObject = stream;
        try {{
          audioCtx = new (window.AudioContext || window.webkitAudioContext)();
          const src = audioCtx.createMediaStreamSource(stream);
          analyser = audioCtx.createAnalyser();
          analyser.fftSize = 512;
          src.connect(analyser);
          const data = new Uint8Array(analyser.frequencyBinCount);
          const tick = () => {{
            analyser.getByteTimeDomainData(data);
            let sum = 0; for (let i=0;i<data.length;i++) {{ const v = (data[i]-128)/128; sum += v*v; }}
            const rms = Math.sqrt(sum/data.length);
            if (rms > 0.04) avatarEl.classList.add('speaking'); else avatarEl.classList.remove('speaking');
            raf = requestAnimationFrame(tick);
          }};
          tick();
        }} catch (err) {{ console.warn('Analyser init failed', err); }}
      }};
      dc = pc.createDataChannel('oai-events');
      dc.onopen = () => {{
        logRaw('data channel open', 'info');
        try {{
          // Ensure the server sends text along with audio
          dc.send(JSON.stringify({{
            type: 'session.update',
            session: {{ modalities: ['audio','text'] }}
          }}));
        }} catch(e){{}}
        try {{
          // Strengthen system prompt so the assistant uses search and image tools
          dc.send(JSON.stringify({{
            type:'session.update',
            session:{{
              tool_choice: 'auto',
              instructions: 'You are Alita, a helpful live voice assistant running inside AlitaOS. You CAN and SHOULD use web search for any query that is time-sensitive or requires current information. Emit either search("<concise query>") or a JSON object {{"query":"...","provider":"tavily|duckduckgo","max_results":6}} as text output so the UI can run the tool. Do this for: latest news on X, current price of Y, current time in Z, weather in Z today, sports scores, CEO/current leadership now, market open status today, etc. Do not say you cannot provide real-time information; instead, output the JSON payload and wait for results. When the user asks for an image, emit a JSON object with {{"prompt":"...","size":"small|medium|large" (or pixel size), "style":"<optional>"}}. Keep spoken summaries concise and cite sources by domain in speech after search results are shown.'
            }}
          }}));
        }} catch(e){{}}
      }};
      dc.onmessage = (evt) => {{
        // Record last event for dedupe context
        try {{ window.__lastEventRaw = evt.data; }} catch {{}}
        try {{
          const msg = JSON.parse(evt.data);
          try {{ window.__lastEvent = msg; }} catch {{}}
          try {{
            if (msg && typeof msg.type === 'string') {{
              if (msg.type === 'response.created') {{ try {{ window.__activeResponseId = (msg.response && msg.response.id) || null; }} catch {{}} }}
              if (msg.type === 'response.done') {{ try {{ window.__activeResponseId = null; }} catch {{}} }}
            }}
          }} catch {{}}
          logRaw(msg, 'dc.onmessage');
          if (tryHandleTool(msg)) return;
          const text = extractTextFromEvent(msg);
          if (text) appendLine('assistant', text);
        }} catch (e) {{
          if (typeof evt.data === 'string' && evt.data.trim()) {{ appendLine('assistant', evt.data); logRaw(evt.data, 'dc.onmessage(text)'); }}
        }}
      }};
      pc.ondatachannel = (evt) => {{
        const ch = evt.channel;
        ch.onmessage = (e) => {{
          try {{ window.__lastEventRaw = e.data; }} catch {{}}
          try {{
            const j = JSON.parse(e.data);
            try {{ window.__lastEvent = j; }} catch {{}}
            try {{
              if (j && typeof j.type === 'string') {{
                if (j.type === 'response.created') {{ try {{ window.__activeResponseId = (j.response && j.response.id) || null; }} catch {{}} }}
                if (j.type === 'response.done') {{ try {{ window.__activeResponseId = null; }} catch {{}} }}
              }}
            }} catch {{}}
            logRaw(j, 'pc.ondatachannel');
            if (tryHandleTool(j)) return;
            const t = extractTextFromEvent(j);
            if (t) appendLine('assistant', t);
          }} catch {{
            if (typeof e.data === 'string' && e.data.trim()) {{ appendLine('assistant', e.data); logRaw(e.data, 'pc.ondatachannel(text)'); }}
          }}
        }}
      }}
      const offer = await pc.createOffer({{offerToReceiveAudio: true}});
      logRaw('created offer SDP', 'sdp');
      await pc.setLocalDescription(offer);

      const configuredProxy = '{proxy_url}';
      let sdpUrl;
      try {{
        const u = new URL(configuredProxy, window.location.origin);
        if (window.location.protocol === 'https:' && u.protocol !== 'https:') {{
          u.protocol = 'https:';
        }}
        sdpUrl = u.toString().replace(/\/$/, '') + '/sdp';
      }} catch (e) {{
        sdpUrl = (window.location.protocol === 'https:' ? 'https://' : 'http://') + 'localhost:8787/sdp';
      }}

      async function postSdp(url) {{
        return fetch(url, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/sdp' }},
          body: offer.sdp
        }});
      }}

      let resp;
      try {{
        logRaw(`POST ${{sdpUrl}}`, 'sdp');
        resp = await postSdp(sdpUrl);
      }} catch (e) {{
        try {{
          const u2 = new URL(sdpUrl);
          u2.protocol = (u2.protocol === 'https:') ? 'http:' : 'https:';
          const alt = u2.toString();
          logRaw(`retry POST ${{alt}}`, 'sdp');
          resp = await postSdp(alt);
        }} catch (e2) {{
          try {{
            const u3 = new URL(sdpUrl);
            u3.hostname = (u3.hostname === 'localhost') ? '127.0.0.1' : 'localhost';
            const alt2 = u3.toString();
            logRaw(`retry POST ${{alt2}}`, 'sdp');
            resp = await postSdp(alt2);
          }} catch (e3) {{ throw e3; }}
        }}
      }}
      if (!resp.ok) {{ logRaw(`SDP failed ${{resp.status}}`, 'error'); throw new Error('SDP exchange failed: ' + resp.status); }}
      const answerSdp = await resp.text();
      await pc.setRemoteDescription({{type: 'answer', sdp: answerSdp}});
      statusEl.textContent = 'Live (listening)';
      logRaw('set remote description', 'sdp');
    }} catch (err) {{
      console.error(err);
      logRaw(String(err), 'error');
      statusEl.textContent = 'Error: ' + err;
      startBtn.disabled = false; stopBtn.disabled = true;
    }}
  }}

  async function stop() {{
    stopBtn.disabled = true; startBtn.disabled = false; statusEl.textContent = 'Stopped';
    try {{
      if (pc) {{ pc.getSenders().forEach(s => s.track && s.track.stop()); pc.close(); }}
      if (micStream) {{ micStream.getTracks().forEach(t => t.stop()); }}
      remoteAudio.srcObject = null;
      if (raf) cancelAnimationFrame(raf);
      if (audioCtx) try {{ audioCtx.close(); }} catch(e){{}}
    }} catch (e) {{ console.warn(e); }}
  }}

  startBtn.onclick = start; stopBtn.onclick = stop;
</script>
        """,
        height=650,
        width=1060,
    )

def handle_image_generation():
    """Handle image generation"""
    st.subheader("🖼️ Image Generation")

    prompt = st.text_area(
        "Describe the image you want to create:",
        placeholder="A futuristic city at sunset with flying cars...",
        height=100
    )

    if st.button("🎨 Generate Image", type="primary"):
        if prompt:
            with st.spinner("Creating your image..."):
                try:
                    result = generate_image(prompt)
                    if result.get("success"):
                        st.success("Image generated successfully!")
                        # Display the image (prefer saved path, fallback to URL)
                        img_path = result.get("path") or result.get("image_path")
                        if img_path and os.path.exists(img_path):
                            st.image(img_path, caption=prompt, use_container_width=True)
                            with open(img_path, "rb") as f:
                                st.download_button(
                                    label="⬇️ Download Image",
                                    data=f.read(),
                                    file_name=os.path.basename(img_path),
                                    mime="image/png",
                                )
                        elif result.get("url"):
                            st.image(result["url"], caption=prompt, use_container_width=True)
                    else:
                        st.error(f"Image generation failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error generating image: {str(e)}")
        else:
            st.warning("Please enter a description for the image.")

    with st.expander("💡 Tips", expanded=False):
        st.markdown(
            """
            - Be specific and descriptive
            - Mention style, colors, and mood
            - Include composition details
            - Specify art style if desired
            """
        )

def handle_information_search():
    """Handle information search"""
    st.subheader("🔍 Information Search")
    
    query = st.text_input(
        "What would you like to know?",
        placeholder="Latest developments in AI technology..."
    )
    
    if st.button("🔍 Search", type="primary"):
        if query:
            with st.spinner("Searching for information..."):
                try:
                    result = search_information(query)
                    if result.get("success"):
                        st.success("Search completed!")
                        st.markdown("### Results:")
                        # search_information returns {"success": bool, "answer": str}
                        st.markdown(result.get("answer", "No results found."))
                    else:
                        st.error(f"Search failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error during search: {str(e)}")
        else:
            st.warning("Please enter a search query.")

def handle_stock_prices():
    """Handle stock price queries"""
    st.subheader("📈 Stock Prices")

    symbol = st.text_input(
        "Stock Symbol:",
        placeholder="AAPL, GOOGL, TSLA...",
        value="AAPL"
    ).upper()

    if st.button("📊 Get Price", type="primary"):
        if symbol:
            with st.spinner(f"Fetching {symbol} data..."):
                try:
                    result = get_stock_price(symbol)
                    if result.get("success"):
                        data = result.get("data", {})
                        st.success(f"Stock data for {symbol}:")

                        # Display key metrics
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Current Price", f"${data.get('current_price', 'N/A')}")
                        with col_b:
                            st.metric("Change", f"{data.get('change', 'N/A')}")
                        with col_c:
                            st.metric("Volume", f"{data.get('volume', 'N/A')}")

                        # Additional info
                        if data.get("info"):
                            st.markdown("### Additional Information:")
                            st.markdown(data["info"])
                    else:
                        st.error(f"Failed to get stock data: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error fetching stock data: {str(e)}")
        else:
            st.warning("Please enter a stock symbol.")

    with st.expander("📊 Popular Stocks", expanded=False):
        st.markdown(
            """
            - AAPL — Apple Inc.
            - GOOGL — Alphabet Inc.
            - MSFT — Microsoft Corp.
            - TSLA — Tesla Inc.
            - AMZN — Amazon.com Inc.
            - NVDA — NVIDIA Corp.
            """
        )

def handle_data_visualization():
    """Handle data visualization"""
    st.subheader("📊 Data Visualization")
    
    # Sample data options
    data_option = st.selectbox(
        "Choose data to visualize:",
        ["Custom Data", "Sample Sales Data", "Sample Stock Performance", "Random Data"]
    )
    
    if data_option == "Custom Data":
        st.markdown("### Upload your data:")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head())
                
                if st.button("📈 Create Chart"):
                    # Simple auto-chart creation
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if len(numeric_cols) >= 2:
                        fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Need at least 2 numeric columns for visualization")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    else:
        # Generate sample data
        if st.button("📊 Generate Chart", type="primary"):
            with st.spinner("Creating visualization..."):
                try:
                    if data_option == "Sample Sales Data":
                        # Create sample sales data
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
                        sales = [100, 120, 140, 110, 160, 180]
                        fig = go.Figure(data=go.Bar(x=months, y=sales))
                        fig.update_layout(title="Monthly Sales Data")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif data_option == "Sample Stock Performance":
                        # Create sample stock chart
                        import numpy as np
                        dates = pd.date_range('2024-01-01', periods=30)
                        prices = np.cumsum(np.random.randn(30)) + 100
                        fig = go.Figure(data=go.Scatter(x=dates, y=prices, mode='lines'))
                        fig.update_layout(title="Stock Price Trend")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    else:  # Random Data
                        # Create random visualization
                        import numpy as np
                        x = np.random.randn(100)
                        y = np.random.randn(100)
                        fig = px.scatter(x=x, y=y, title="Random Data Scatter Plot")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.success("Chart created successfully!")
                except Exception as e:
                    st.error(f"Error creating chart: {str(e)}")
    
    # Tips expander for guidance
    with st.expander("💡 Tips", expanded=False):
        st.markdown(
            """
            - Upload a CSV for custom charts or use sample datasets
            - Ensure your file has at least two numeric columns for scatter plots
            - Use the sidebar to switch tools quickly
            - All charts are rendered with responsive width for better layout
            """
        )

def handle_python_code():
    """Handle Python code creation and execution"""
    st.subheader("🐍 Python Code")
    
    tab1, tab2 = st.tabs(["💻 Code Editor", "📁 File Creator"])
    
    with tab1:
        st.markdown("### Execute Python Code")
        
        code = st.text_area(
            "Enter your Python code:",
            value="""# Example: Simple calculation
import math

def calculate_circle_area(radius):
    return math.pi * radius ** 2

radius = 5
area = calculate_circle_area(radius)
print(f"Circle with radius {radius} has area: {area:.2f}")
""",
            height=200
        )
        
        if st.button("▶️ Run Code", type="primary"):
            if code:
                with st.spinner("Executing code..."):
                    try:
                        result = execute_python_code(code)
                        if result.get("success"):
                            st.success("Code executed successfully!")
                            if result.get("output"):
                                st.code(result["output"], language="text")
                        else:
                            st.error(f"Execution failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error executing code: {str(e)}")
            else:
                st.warning("Please enter some Python code.")
    
    with tab2:
        st.markdown("### Create Python File")
        
        topic = st.text_input(
            "What should the Python file do?",
            placeholder="Create a web scraper, data analyzer, game, etc."
        )
        
        filename = st.text_input(
            "Filename:",
            placeholder="my_script.py"
        )
        
        if st.button("📝 Create File", type="primary"):
            if topic and filename:
                with st.spinner("Creating Python file..."):
                    try:
                        result = create_python_file(topic, filename)
                        if result.get("success"):
                            st.success(f"File '{filename}' created successfully!")
                            if result.get("code"):
                                st.code(result["code"], language="python")
                        else:
                            st.error(f"File creation failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error creating file: {str(e)}")
            else:
                st.warning("Please enter both topic and filename.")
    
    # Tips expander for code section
    with st.expander("💡 Tips", expanded=False):
        st.markdown(
            """
            - Use the Code Editor tab to quickly run snippets
            - The File Creator tab will generate starter code via the AI
            - Always review generated code before running
            - Avoid long-running or network-heavy operations in the demo environment
            """
        )

def main():
    """Main application function"""
    initialize_session_state()
    display_header()

    # Get selected tool from the top navbar (no sidebar)
    selected_tool = get_selected_tool()
    
    # Handle the selected tool
    if selected_tool == "🎧 Live Assistant":
        handle_live_assistant()
    elif selected_tool == "💬 Chat Assistant":
        handle_chat_assistant()
    elif selected_tool == "🖼️ Image Generation":
        handle_image_generation()
    elif selected_tool == "🔍 Information Search":
        handle_information_search()
    elif selected_tool == "📈 Stock Prices":
        handle_stock_prices()
    elif selected_tool == "📊 Data Visualization":
        handle_data_visualization()
    elif selected_tool == "🐍 Python Code":
        handle_python_code()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🤖 <strong>AlitaOS</strong> - Powered by OpenAI | 
        <a href="https://github.com/openai" target="_blank">OpenAI API</a> | 
        Built with ❤️ using Streamlit
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
