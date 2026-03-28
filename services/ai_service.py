"""
Nexus AI – AI Service
======================
Unified interface for Groq (primary) and OpenAI (fallback)
API calls. Supports text chat and vision (image analysis)
via Groq's llama-3.2-90b-vision-preview model.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

GROQ_TEXT_MODEL = "llama-3.2-90b-vision-preview"
GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"
OPENAI_MODEL = "gpt-4o"

SYSTEM_PROMPT = (
    "You are Nexus AI, an advanced Digital Twin assistant. "
    "You help users by answering questions, analysing documents and images, "
    "and providing intelligent insights. Be concise, accurate, and helpful."
)


class AIService:
    """Handles all AI model interactions with automatic fallback."""

    def __init__(self):
        self.groq_key: str = os.getenv("GROQ_API_KEY", "")
        self.openai_key: str = os.getenv("OPENAI_API_KEY", "")
        self.timeout = 60.0

    # ── Public API ──────────────────────────────────────────────

    def generate_response(
        self,
        message: str,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate an AI response for the given user message.

        Args:
            message: The user's text input.
            file_path: Optional path to an image for vision analysis.

        Returns:
            dict with keys: ``response`` (str), ``usage`` (dict with
            prompt_tokens, completion_tokens, total_tokens).
        """
        # Try Groq first, then fall back to OpenAI
        if self.groq_key:
            try:
                return self._call_groq(message, file_path)
            except Exception as exc:
                logger.warning("Groq API failed (%s), falling back to OpenAI.", exc)

        if self.openai_key:
            try:
                return self._call_openai(message, file_path)
            except Exception as exc:
                logger.error("OpenAI API also failed: %s", exc)
                raise

        raise RuntimeError(
            "No AI API key configured. Set GROQ_API_KEY or OPENAI_API_KEY."
        )

    # ── Groq ────────────────────────────────────────────────────

    def _call_groq(self, message: str, file_path: str | None) -> dict:
        messages = self._build_messages(message, file_path)
        model = GROQ_VISION_MODEL if file_path else GROQ_TEXT_MODEL

        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(GROQ_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return self._parse_response(data)

    # ── OpenAI ──────────────────────────────────────────────────

    def _call_openai(self, message: str, file_path: str | None) -> dict:
        messages = self._build_messages(message, file_path)

        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(OPENAI_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return self._parse_response(data)

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _build_messages(message: str, file_path: str | None) -> list[dict]:
        """Build the messages array, optionally including an image."""
        system = {"role": "system", "content": SYSTEM_PROMPT}

        if file_path and os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower().lstrip(".")
            mime = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
            }.get(ext)

            if mime:
                with open(file_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                user_content = [
                    {"type": "text", "text": message},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ]
            else:
                # Non-image file: read as text and prepend to message
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_text = f.read(50_000)  # cap at 50 KB
                    user_content = (
                        f"[Attached file content]\n{file_text}\n\n"
                        f"[User message]\n{message}"
                    )
                except Exception:
                    user_content = message
        else:
            user_content = message

        return [system, {"role": "user", "content": user_content}]

    @staticmethod
    def _parse_response(data: dict) -> dict:
        """Normalise the response from Groq / OpenAI format."""
        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})
        return {
            "response": choice.get("message", {}).get("content", ""),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }
