"""Simple information search using AI providers for Streamlit.

Provides `search_information(query)` which calls the configured AI provider to produce a
concise, factual summary and returns a dict suitable for Streamlit.
"""

import os
from utils.common import logger
from utils.ai_models import get_llm
def search_information(query: str):
    """Return information for a query using OpenAI.

    Returns a dict: {"success": bool, "answer": str|None, "error": str|None}
    """
    try:
        logger.info(f"🕵 Searching for information about: '{query}'")
        
        # Get configured AI provider
        llm = get_llm(task="default")
        
        # Use AI provider to provide comprehensive information about the query
        system_prompt = "You are a helpful assistant that provides comprehensive, accurate, and up-to-date information about any topic. Provide detailed answers with relevant facts, context, and explanations."
        
        response_text = llm.invoke(
            prompt=f"Please provide comprehensive information about: {query}",
            system_prompt=system_prompt
        )
        
        return {
            "success": True,
            "answer": response_text,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ Error retrieving information: {str(e)}")
        return {"success": False, "answer": None, "error": str(e)}
