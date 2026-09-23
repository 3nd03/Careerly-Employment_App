import logging
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"


def call_claude(prompt: str, system: str = "") -> str:
    load_dotenv()
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = message.content[0].text
    logger.info(
        "timestamp=%s model=%s prompt_chars=%d response_chars=%d",
        datetime.now().isoformat(), MODEL, len(prompt), len(response_text),
    )
    return response_text
