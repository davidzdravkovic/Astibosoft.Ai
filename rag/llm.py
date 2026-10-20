from __future__ import annotations

import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

SYSTEM_INSTRUCTION = (
    "You are the Astibosoft website assistant. "
    "Answer using the company knowledge context when it is relevant. "
    "Be concise, practical, and honest — do not invent prices, timelines, or guarantees. "
    "If the context is not enough, say so briefly and suggest contacting Astibosoft "
    "via the contact form or hello@astibosoft.com. "
    "When context includes section labels, you may mention which topic it comes from."
)


class LlmError(Exception):
    pass


class LlmNotConfiguredError(LlmError):
    pass


def _build_user_prompt(question: str, context: str) -> str:
    return (
        "Company knowledge context:\n"
        f"{context}\n\n"
        f"Visitor question: {question}\n\n"
        "Answer using the context as your primary source. "
        "Do not invent facts that are not supported by the context."
    )


def generate_answer(question: str, context: str) -> str:
    return _generate_gemini(question, context)


def _generate_gemini(question: str, context: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise LlmNotConfiguredError("GEMINI_API_KEY is not configured on the AI service.")

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    prompt = _build_user_prompt(question, context)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_INSTRUCTION)
        response = model.generate_content(prompt)
    except LlmNotConfiguredError:
        raise
    except Exception as exc:
        logger.exception("Gemini request failed model=%s", model_name)
        detail = str(exc)
        if "404" in detail or "not available" in detail.lower():
            raise LlmError(f"Gemini model '{model_name}' is unavailable.") from exc
        raise LlmError("Gemini request failed. Try again later.") from exc

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise LlmError("Gemini returned an empty response.")

    return text.strip()
