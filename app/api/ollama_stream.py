#!/usr/bin/env python3
"""
Ollama Streaming API Endpoint
Provides server-sent events streaming for Ollama responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from utils.ai_models import get_llm
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Ollama Streaming API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/ollama-stream")
async def ollama_stream(request: Request):
    """Stream Ollama responses in real-time."""
    try:
        body = await request.json()
        message = body.get('message', '')
        model = body.get('model', 'llama2')
        
        if not message:
            return {"error": "No message provided"}
        
        # Get the AI provider (should be Ollama)
        ai_client = get_llm()
        
        async def generate_stream():
            try:
                # Stream the response from Ollama
                for chunk in ai_client.stream(
                    prompt=message,
                    system_prompt="You are a helpful AI assistant. Provide clear, concise responses suitable for voice conversation."
                ):
                    if chunk:
                        # Format as server-sent event
                        data = json.dumps({"content": chunk})
                        yield f"data: {data}\n\n"
                        
                        # Small delay to prevent overwhelming the client
                        await asyncio.sleep(0.01)
                
                # Send completion signal
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8788)
