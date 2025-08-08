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
from dotenv import load_dotenv
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
    max-width: 1200px;
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

    # Provide Start/Stop UI with transcript and animated avatar
    st_html(
        fr"""
<style>
  :root {{
    /* inherit globals from page: light theme */
  }}
  #container {{
    margin: 0 auto; width: 100%; max-width: 760px; background: var(--panel); padding: 14px; border-radius: 12px; border:1px solid var(--border);
  }}
  #alita-wrap {{ display:flex; align-items:center; gap:16px; margin-bottom:14px; }}
  #avatar {{ width:84px; height:84px; border-radius:50%; object-fit:cover; box-shadow:0 0 0px rgba(111,125,255,0.0); transition: box-shadow 160ms ease; border:2px solid var(--border); background:#ddd; }}
  #avatar.speaking {{ box-shadow:0 0 22px rgba(111,125,255,0.55); }}
  #controls {{ display:flex; align-items:center; gap:10px; }}
  #controls button {{
    appearance:none; border:none; padding:10px 16px; border-radius:10px; font-weight:600; cursor:pointer; color:#fff;
    background: linear-gradient(90deg, var(--acc) 0%, var(--acc2) 100%);
  }}
  #controls button#start {{ border:1px solid rgba(0,0,0,0.04); }}
  #controls button#stop {{ border:1px solid rgba(0,0,0,0.04); }}
  #controls button[disabled] {{ opacity:0.5; cursor:not-allowed; }}
  #status {{ margin-left:8px; color: var(--muted); font-size: 13px; }}
  #transcript {{ border:1px solid var(--border); border-radius:12px; padding:10px; height:clamp(220px, 32vh, 600px); overflow:auto; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:var(--panel-2); color: var(--text); }}
  .msg {{ display:block; max-width: 100%; padding:8px 10px; border-radius:12px; margin:6px 0; line-height:1.45; white-space:pre-wrap; }}
  .u {{ background:#eceef2; color: var(--text); border:1px solid var(--border); }}
  .a {{ background:#f5f6f8; color: var(--text); border:1px solid var(--border); }}
  .role {{ display:block; font-size:11px; color: var(--muted); margin-bottom:4px; }}
</style>
<div id=container>
  <div id=alita-wrap>
    <img id=avatar src="{avatar_src}" alt="Alita Avatar" onerror="this.onerror=null; this.src='https://placehold.co/84x84?text=Alita';" />
    <div id=controls>
      <button id=start>Start</button>
      <button id=stop disabled>Stop</button>
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
<script>
  const startBtn = document.getElementById('start');
  const stopBtn = document.getElementById('stop');
  const statusEl = document.getElementById('status');
  const remoteAudio = document.getElementById('remoteAudio');
  const transcriptEl = document.getElementById('transcript');
  const avatarEl = document.getElementById('avatar');
  const rawLogEl = document.getElementById('rawlog');
  let pc, micStream;
  let dc; // data channel
  let analyser, audioCtx, raf;

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
      // Streaming deltas
      if ((evt.type && evt.type.endsWith('.delta')) && typeof evt.delta === 'string') {{
        return evt.delta;
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

  async function start() {{
    startBtn.disabled = true; stopBtn.disabled = false; statusEl.textContent = 'Starting…';
    try {{
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
        try {{ dc.send(JSON.stringify({{type:'response.create', response:{{instructions:'You are Alita, a helpful live voice assistant.'}}}})); }} catch(e){{}}
      }};
      dc.onmessage = (evt) => {{
        try {{
          const msg = JSON.parse(evt.data);
          logRaw(msg, 'dc.onmessage');
          const text = extractTextFromEvent(msg);
          if (text) appendLine('assistant', text);
        }} catch (e) {{
          if (typeof evt.data === 'string' && evt.data.trim()) {{ appendLine('assistant', evt.data); logRaw(evt.data, 'dc.onmessage(text)'); }}
        }}
      }};
      pc.ondatachannel = (evt) => {{
        const ch = evt.channel;
        ch.onmessage = (e) => {{
          try {{
            const j = JSON.parse(e.data);
            logRaw(j, 'pc.ondatachannel');
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
        }} catch (e2) {{ throw e2; }}
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
        height=520,
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
                        st.markdown(result.get("response", "No results found."))
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
