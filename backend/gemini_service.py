"""
gemini_service.py

Servizio di integrazione con Gemini API.
Supporta generazione di contenuti a partire da:
  - immagini (JPEG, PNG, WEBP, HEIC/HEIF)
  - documenti PDF

Il file può essere inviato a Gemini come `inline_data` con il mime_type
corretto: Gemini gestisce nativamente sia immagini che PDF senza bisogno
di conversioni lato client.
"""

import base64
import json
import logging
from typing import Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Mime types accettati per l'invio a Gemini.
# Seconda barriera di validazione, indipendente da quella in main.py.
SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/pdf",
}

DEFAULT_MODEL = "gemini-1.5-flash"


class GeminiServiceError(Exception):
    """Errore generico del servizio Gemini."""
    pass


def _validate_mime_type(mime_type: str) -> None:
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError(
            f"Tipo di file non supportato: '{mime_type}'. "
            f"Tipi supportati: {', '.join(sorted(SUPPORTED_MIME_TYPES))}"
        )


def _validate_file_size(file_bytes: bytes, max_file_size_mb: float) -> None:
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_file_size_mb:
        raise ValueError(
            f"File troppo grande: {size_mb:.2f} MB "
            f"(limite massimo: {max_file_size_mb} MB)"
        )


def _build_config(temperature: float = 0.4, max_output_tokens: int = 4096) -> dict:
    return {
        "temperature": temperature,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": max_output_tokens,
        "response_mime_type": "application/json",
    }


def _extract_text(response) -> str:
    """Estrae il testo dalla risposta di Gemini, con gestione errori robusta."""
    try:
        return response.text
    except Exception as exc:
        logger.error("Impossibile estrarre il testo dalla risposta Gemini: %s", exc)
        raise GeminiServiceError(
            "La risposta di Gemini non contiene testo valido. "
            "Possibile blocco per safety filter o risposta vuota."
        ) from exc


def generate_from_file(
    file_bytes: bytes,
    mime_type: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_file_size_mb: float = 10.0,
    temperature: float = 0.4,
    max_output_tokens: int = 4096,
) -> str:
    """
    Genera contenuto a partire da un file (immagine o PDF) e un prompt testuale.

    Gestisce in modo unificato immagini e PDF: il file viene inviato a Gemini
    come inline_data con il mime_type corretto, senza alcuna conversione
    lato client. Gemini elabora nativamente entrambi i formati.

    Args:
        file_bytes: contenuto binario del file (immagine o PDF).
        mime_type: mime type del file (es. "image/jpeg", "application/pdf").
        prompt: istruzioni testuali da associare al file.
        model: nome del modello Gemini da utilizzare.
        max_file_size_mb: dimensione massima consentita per il file.
        temperature: temperatura di generazione.
        max_output_tokens: numero massimo di token in output.

    Returns:
        Testo generato da Gemini (tipicamente una stringa JSON).

    Raises:
        ValueError: se il mime_type non è supportato o il file supera la dimensione massima.
        GeminiServiceError: se la chiamata a Gemini fallisce o la risposta è invalida.
    """
    _validate_mime_type(mime_type)
    _validate_file_size(file_bytes, max_file_size_mb)

    try:
        generative_model = genai.GenerativeModel(model)

        file_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(file_bytes).decode("utf-8"),
            }
        }

        response = generative_model.generate_content(
            [file_part, prompt],
            generation_config=_build_config(temperature, max_output_tokens),
        )

        return _extract_text(response)

    except ValueError:
        # ri-solleva gli errori di validazione senza wrapparli
        raise
    except Exception as exc:
        logger.error("Errore durante la chiamata a Gemini: %s", exc)
        raise GeminiServiceError(f"Errore durante la generazione: {exc}") from exc


def generate_text(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.4,
    max_output_tokens: int = 4096,
) -> str:
    """
    Genera contenuto a partire da un prompt testuale, senza file allegato.
    Utile per l'endpoint /evaluate.
    """
    try:
        generative_model = genai.GenerativeModel(model)

        response = generative_model.generate_content(
            prompt,
            generation_config=_build_config(temperature, max_output_tokens),
        )

        return _extract_text(response)

    except Exception as exc:
        logger.error("Errore durante la chiamata a Gemini (generate_text): %s", exc)
        raise GeminiServiceError(f"Errore durante la generazione: {exc}") from exc


def parse_json_response(raw_text: str) -> dict:
    """
    Effettua il parsing sicuro di una risposta JSON generata da Gemini,
    con gestione di eventuali code fence markdown residui.
    """
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Impossibile fare il parsing del JSON: %s\nContenuto: %s", exc, cleaned)
        raise GeminiServiceError(
            "La risposta di Gemini non è un JSON valido."
        ) from exc


# Alias di retrocompatibilità: mantiene funzionante il codice esistente
# (es. main.py) che chiama ancora il vecchio nome della funzione.
generate_from_image = generate_from_file
