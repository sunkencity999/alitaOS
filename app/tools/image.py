"""Image generation tool for Streamlit.

Provides a simple function `generate_image(prompt)` that uses OpenAI's
Images API (DALL·E) to generate an image, saves it to the scratch pad,
and returns a structured result for the Streamlit UI.

Note: Image generation currently requires OpenAI as Ollama doesn't support image generation.
"""

import os
from openai import OpenAI
from utils.common import logger, scratch_pad_dir
from utils.ai_models import get_llm

def generate_image(prompt: str):
    """Generate an image from a prompt using OpenAI DALL·E and save to disk.

    Returns a dict:
    {"success": bool, "path": str | None, "url": str | None, "error": str | None}
    """
    try:
        logger.info(f"🌄 Generating image based on prompt: '{prompt}'")

        # Image generation requires OpenAI (DALL-E)
        # Check if we can use the configured AI provider for prompt enhancement
        try:
            llm = get_llm(task="image_prompt")
            if llm.provider == "ollama":
                # Use Ollama to enhance the prompt, but still use OpenAI for image generation
                enhanced_prompt = llm.invoke(
                    prompt=f"Enhance this image generation prompt to be more detailed and artistic: {prompt}",
                    system_prompt="You are an expert at creating detailed, artistic image generation prompts. Enhance the given prompt with vivid details, artistic style, and composition suggestions while keeping the core concept intact."
                )
                prompt = enhanced_prompt
        except Exception as e:
            logger.warning(f"Could not enhance prompt with AI provider: {e}")
        
        # Initialize OpenAI client for image generation
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        # Generate image using DALL·E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url

        # Download and save the image
        import requests
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        os.makedirs(scratch_pad_dir, exist_ok=True)
        img_path = os.path.join(scratch_pad_dir, "generated_image.png")

        with open(img_path, "wb") as f:
            f.write(img_response.content)

        logger.info(f"🖼️ Image generated and saved successfully at {img_path}")
        return {"success": True, "path": img_path, "url": image_url}

    except Exception as e:
        logger.error(f"❌ Error generating image: {str(e)}")
        return {"success": False, "path": None, "url": None, "error": str(e)}
