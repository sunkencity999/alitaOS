"""Python code utilities for Streamlit.

Exposes two functions used by the Streamlit UI:
- create_python_file(topic, filename) → generates a Python file using OpenAI and saves it.
- execute_python_code(code) → executes arbitrary Python code and returns stdout/stderr.
"""

import os
import subprocess
from openai import OpenAI
from utils.common import logger, scratch_pad_dir


def _generate_code_with_openai(topic: str) -> str:
    """Use OpenAI to draft Python code for the topic."""
    client = OpenAI()
    system_msg = (
        "You are a senior Python engineer. Generate a concise, well-structured,\n"
        "and well-commented Python script for the user's topic. Include a\n"
        "top-level docstring, functions, and a simple __main__ example."
    )
    user_msg = f"Topic: {topic}\nReturn only code in a single Python file."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=1200,
    )
    content = resp.choices[0].message.content or ""
    # Strip code fences if present
    stripped = content.strip()
    if stripped.startswith("```"):
        # handle ```python or ```
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1 :]
        stripped = content.strip()
        if stripped.endswith("```"):
            content = content.rsplit("```", 1)[0]
    return content


def create_python_file(topic: str, filename: str):
    """Create a Python file for a given topic using OpenAI.

    Returns dict: {"success": bool, "path": str|None, "code": str|None, "error": str|None}
    """
    try:
        logger.info(f"📝 Drafting Python file for topic: '{topic}'")
        code = _generate_code_with_openai(topic)

        os.makedirs(scratch_pad_dir, exist_ok=True)
        filepath = os.path.join(scratch_pad_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        logger.info(f"💾 Python file '{filename}' created successfully at {filepath}")
        return {"success": True, "path": filepath, "code": code}

    except Exception as e:
        logger.error(f"❌ Error creating Python file: {str(e)}")
        return {"success": False, "path": None, "code": None, "error": str(e)}


def execute_python_code(code: str):
    """Execute Python code in a subprocess and return stdout/stderr.

    Returns dict: {"success": bool, "output": str|None, "error": str|None}
    """
    try:
        # Write to a temporary file in scratch pad for isolated execution
        os.makedirs(scratch_pad_dir, exist_ok=True)
        temp_path = os.path.join(scratch_pad_dir, "_temp_exec.py")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("✅ Python code executed successfully")
            return {"success": True, "output": result.stdout}
        else:
            logger.error(f"❌ Python code execution failed: {result.stderr}")
            return {"success": False, "error": result.stderr}

    except Exception as e:
        logger.error(f"❌ Error executing Python code: {str(e)}")
        return {"success": False, "error": str(e)}
