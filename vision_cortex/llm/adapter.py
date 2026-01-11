"""Simple LLM adapter with OpenAI fallback to a deterministic mock.

This adapter exposes `call(prompt)` to get a string response.
If `OPENAI_API_KEY` is set in the environment, it will call OpenAI's completion API.
Otherwise, it returns a canned response for local testing.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")


def call(prompt: str, max_tokens: int = 256) -> str:
    if OPENAI_KEY:
        try:
            import openai

            openai.api_key = OPENAI_KEY
            resp = openai.ChatCompletion.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.exception("OpenAI call failed: %s", e)
            return f"[llm_error] {e}"

    # Mock deterministic response for offline testing
    return f"MOCK_RESPONSE: Received prompt, length={len(prompt)}"
