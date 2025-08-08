#!/usr/bin/env python3
"""
FastAPI proxy to OpenAI Realtime WebRTC SDP exchange.
Keeps API key on the server and returns the SDP answer to the browser.

Endpoint:
  POST /sdp    Content-Type: application/sdp, Body: offer SDP
  -> forwards to OpenAI Realtime and returns answer SDP (text/plain)

Usage (dev):
  uvicorn app.realtime_proxy:app --host 127.0.0.1 --port 8787

For HTTPS (self-signed):
  uvicorn app.realtime_proxy:app --host 127.0.0.1 --port 8787 \
    --ssl-keyfile .cert/key.pem --ssl-certfile .cert/cert.pem
"""
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_MODEL = os.getenv("OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview-2024-12-17")
OPENAI_REALTIME_URL = f"https://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}"

app = FastAPI(title="AlitaOS Realtime Proxy")

# Allow localhost origins (HTTP/HTTPS) for Streamlit UI
ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "https://localhost:8501",
    "http://127.0.0.1:8501",
    "https://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["http://localhost", "https://localhost", "http://127.0.0.1", "https://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health():
    return {"status": "ok", "model": OPENAI_REALTIME_MODEL}

@app.post("/sdp")
async def sdp(request: Request):
    if not OPENAI_API_KEY:
        return Response(content="OPENAI_API_KEY not configured", media_type="text/plain", status_code=500)

    offer_sdp = await request.body()
    try:
        resp = requests.post(
            OPENAI_REALTIME_URL,
            data=offer_sdp,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/sdp",
                "OpenAI-Beta": "realtime=v1",
            },
            timeout=30,
        )
        return Response(content=resp.text, media_type="application/sdp", status_code=resp.status_code)
    except Exception as e:
        return Response(content=f"Proxy error: {e}", media_type="text/plain", status_code=500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ALITA_REALTIME_PORT", "8787"))
    uvicorn.run("app.realtime_proxy:app", host="127.0.0.1", port=port, reload=False)
