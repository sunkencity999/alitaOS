"""Image generation tool for Streamlit.

Provides a simple function `generate_image(prompt)` that uses OpenAI's
Images API (DALL·E) to generate an image, saves it to the scratch pad,
and returns a structured result for the Streamlit UI.
"""

import os
from openai import OpenAI
from utils.common import logger, scratch_pad_dir

def generate_image(prompt: str):
    """Generate an image from a prompt using OpenAI DALL·E and save to disk.

    Returns a dict:
    {"success": bool, "path": str | None, "url": str | None, "error": str | None}
    """
    try:
        logger.info(f"🌄 Generating image based on prompt: '{prompt}'")

        # Initialize OpenAI client
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
