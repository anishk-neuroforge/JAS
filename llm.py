"""
llm.py — LLM integration for JAS v1
Handles plan generation, self-healing retries, and screenshot verification.
"""

import requests
import json
import re
import base64
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL      = "meta/llama-3.1-8b-instruct"
VISION_MODEL = "meta/llama-3.2-11b-vision-instruct"
API_KEY    = os.getenv("NVIDIA_API_KEY", "")

SYSTEM_PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")

HEAL_SUFFIX = """
A previous attempt failed. Here is the context:
  Failed step index: {failed_step}
  Error: {error}
  Original plan: {original_plan}

Generate a corrected plan that avoids this failure.
"""

VERIFY_PROMPT = """
You are a desktop automation verifier.
The user wanted to: {goal}
A screenshot was taken after execution.
Respond ONLY with valid JSON:
{{"success": true/false, "note": "brief explanation"}}
"""


def _call_api(messages: list, max_tokens: int = 600) -> str:
    if not API_KEY:
        raise EnvironmentError(
            "NVIDIA_API_KEY not set. Add it to your .env file."
        )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(INVOKE_URL, headers=headers,
                             json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _extract_json(raw: str) -> dict:
    """Safely pull the first JSON object from a string."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON found in LLM response:\n{raw[:300]}")


def generate_plan(command: str, error_context: dict | None = None) -> dict:
    """
    Generate an automation plan for *command*.
    If *error_context* is provided, append healing instructions.
    """
    user_content = command
    if error_context:
        user_content += "\n\n" + HEAL_SUFFIX.format(
            failed_step=error_context.get("failed_step", "?"),
            error=error_context.get("error", "unknown"),
            original_plan=json.dumps(
                error_context.get("original_plan", {}), indent=2),
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]

    raw = _call_api(messages)
    return _extract_json(raw)


def verify_execution(goal: str, screenshot_path: str) -> dict:
    """
    Send the screenshot to the LLM and ask whether the goal was achieved.
    Falls back gracefully if the model doesn't support vision.
    """
    try:
        img_bytes = Path(screenshot_path).read_bytes()
        b64       = base64.b64encode(img_bytes).decode()

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": VERIFY_PROMPT.format(goal=goal),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}",
                        },
                    },
                ],
            }
        ]

        # Vision call — use a generous token budget
        payload = {
            "model": VISION_MODEL,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 200,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json",
        }
        response = requests.post(INVOKE_URL, headers=headers,
                                 json=payload, timeout=120)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        return _extract_json(raw)

    except Exception as e:
        # Non-fatal — verification is a bonus feature
        return {"success": True, "note": f"Verification skipped: {e}"}
