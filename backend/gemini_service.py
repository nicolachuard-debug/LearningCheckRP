from google import genai
from google.genai import types
from config import GEMINI_API_KEY

_client = None
DEFAULT_MODEL = "gemini-3-flash"  # fallback: "gemini-3.1-flash-lite"


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY non impostata: impossibile usare Gemini.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def generate_text(prompt: str, model_name: str = DEFAULT_MODEL) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text


def generate_from_image(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg", model: str = DEFAULT_MODEL) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        ]
    )
    return response.text
