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


def generate_text(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    _ensure_configured()
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text