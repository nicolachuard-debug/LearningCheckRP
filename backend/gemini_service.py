import logging
import mimetypes
from typing import Optional

from google import genai
from google.genai import types

from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

_client = None

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_MIME_TYPE = "image/jpeg"
DEFAULT_MAX_IMAGE_SIZE_MB = 20


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY non impostata: impossibile usare Gemini.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _build_config(temperature: Optional[float], max_output_tokens: Optional[int]):
    if temperature is None and max_output_tokens is None:
        return None
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_output_tokens is not None:
        kwargs["max_output_tokens"] = max_output_tokens
    return types.GenerateContentConfig(**kwargs)


def _extract_text(response) -> str:
    if not getattr(response, "candidates", None):
        raise RuntimeError("Risposta vuota da Gemini: nessun candidato restituito (possibile blocco safety).")

    candidate = response.candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError(
            f"Risposta vuota o bloccata da Gemini (finish_reason={finish_reason})."
        )

    return text


def _guess_mime_type(filename: Optional[str], fallback: str = DEFAULT_MIME_TYPE) -> str:
    if not filename:
        return fallback
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or fallback


def generate_text(
    prompt: str,
    model_name: str = DEFAULT_MODEL,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("Il prompt non può essere vuoto.")

    client = _get_client()
    config = _build_config(temperature, max_output_tokens)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
    except Exception as e:
        logger.error("Errore durante la chiamata a Gemini (generate_text): %s", e)
        raise RuntimeError(f"Errore nella chiamata a Gemini: {e}") from e

    return _extract_text(response)


def generate_from_image(
    prompt: str,
    image_bytes: bytes,
    mime_type: Optional[str] = None,
    filename: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    max_image_size_mb: float = DEFAULT_MAX_IMAGE_SIZE_MB,
) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("Il prompt non può essere vuoto.")
    if not image_bytes:
        raise ValueError("image_bytes non può essere vuoto.")

    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_image_size_mb:
        raise ValueError(
            f"Immagine troppo grande ({size_mb:.1f} MB): limite massimo {max_image_size_mb} MB."
        )

    resolved_mime_type = mime_type or _guess_mime_type(filename)

    client = _get_client()
    config = _build_config(temperature, max_output_tokens)

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=resolved_mime_type),
            ],
            config=config,
        )
    except Exception as e:
        logger.error("Errore durante la chiamata a Gemini (generate_from_image): %s", e)
        raise RuntimeError(f"Errore nella chiamata a Gemini: {e}") from e

    return _extract_text(response)
