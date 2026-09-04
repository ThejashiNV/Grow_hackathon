"""Gemini client wrapper -- the only place in the codebase that talks to
Gemini. Never logs or returns the API key; any exception text is scrubbed for
the key before logging, since some SDK errors echo request parameters back.

Called only from the FastAPI backend (rag_service.py). The frontend never
sees GEMINI_API_KEY or a Gemini SDK response directly -- it only gets the
already-composed answer text.
"""

import asyncio
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 15


def _scrub(text: str, key: str) -> str:
    if key and key in text:
        return text.replace(key, "***REDACTED***")
    return text


async def generate_explanation(prompt: str) -> str | None:
    """Returns the model's answer, or None if Gemini is unconfigured or the
    call fails for any reason (missing key, bad model name, timeout, rate
    limit, network error, malformed response). Callers must treat None as
    "fall back to the deterministic evidence summary", never as an error to
    surface to the user."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)

        response = await asyncio.wait_for(
            client.aio.models.generate_content(model=settings.gemini_model, contents=prompt),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        text = getattr(response, "text", None)
        if not text or not text.strip():
            logger.warning("Gemini returned an empty response; falling back")
            return None
        return text.strip()

    except TimeoutError:
        logger.warning("Gemini request timed out after %ss; falling back", REQUEST_TIMEOUT_SECONDS)
        return None
    except Exception as exc:  # noqa: BLE001 -- any SDK/network failure should fall back, never 500
        safe_message = _scrub(str(exc), settings.gemini_api_key)
        logger.warning("Gemini call failed (%s): %s; falling back", type(exc).__name__, safe_message)
        return None
