"""Utilities for interacting with the Gemini API.

This module centralizes client initialization so that the rest of the codebase
shares a single configured client instance. It also provides small helpers for
common text and image generation tasks used across the project.
"""
from __future__ import annotations

from typing import Optional

from google import genai
from google.genai import types

import config

TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "imagen-3.0-generate-002"

_client: Optional[genai.Client] = None


def _ensure_api_key() -> str:
    api_key = getattr(config, "API_KEY", None)
    if not api_key:
        raise RuntimeError("Gemini API key is not configured.")
    return api_key


def get_client() -> genai.Client:
    """Return a shared Gemini client configured with the project API key."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=_ensure_api_key())
    return _client


def generate_text(prompt: str, *, config_override: Optional[types.GenerateContentConfig] = None) -> str:
    """Generate a text response for the provided prompt."""
    response = get_client().models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=config_override,
    )
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


def generate_image(prompt: str, *, config_override: Optional[types.GenerateImagesConfig] = None) -> bytes:
    """Generate an image and return the raw bytes of the first result."""
    generation_config = config_override or types.GenerateImagesConfig(number_of_images=1)
    response = get_client().models.generate_images(
        model=IMAGE_MODEL,
        prompt=prompt,
        config=generation_config,
    )
    images = response.generated_images or []
    if not images or images[0].image is None or images[0].image.image_bytes is None:
        raise RuntimeError("Gemini did not provide image bytes.")
    return images[0].image.image_bytes
