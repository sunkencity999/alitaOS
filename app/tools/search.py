"""Simple information search via OpenAI for Streamlit.

Provides `search_information(query)` which calls OpenAI to produce a
concise, factual summary and returns a dict suitable for Streamlit.
"""

import os
from openai import OpenAI
from utils.common import logger
def search_information(query: str):
    """Return information for a query using OpenAI.

    Returns a dict: {"success": bool, "answer": str|None, "error": str|None}
    """
    try:
        logger.info(f"🕵 Searching for information about: '{query}'")
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Use OpenAI to provide comprehensive information about the query
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides comprehensive, accurate, and up-to-date information about any topic. Provide detailed answers with relevant facts, context, and explanations."
                },
                {
                    "role": "user",
                    "content": f"Please provide comprehensive information about: {query}"
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        search_result = response.choices[0].message.content
        logger.info(f"📏 Information about '{query}' retrieved successfully.")
        return {"success": True, "answer": search_result}
        
    except Exception as e:
        logger.error(f"❌ Error retrieving information: {str(e)}")
        return {"success": False, "answer": None, "error": str(e)}
