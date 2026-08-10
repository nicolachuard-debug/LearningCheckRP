import google.generativeai as genai
from config import GEMINI_API_KEY

_configured = False

def _ensure_configured():
    global _configured
    if not _configured:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY non impostata: impossibile usare Gemini.")
        genai.configure(api_key=GEMINI_API_KEY)
        _configured = True


def generate_text(prompt: str, model_name: str = "gemini-1.5") -> str:
    _ensure_configured()
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text


def generate_from_image(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg", model: str = "gemini-1.5-flash") -> str:
    gemini_model = genai.GenerativeModel(model)
    response = gemini_model.generate_content([
        prompt,
        {"mime_type": mime_type, "data": image_bytes}
    ])
    return response.text
