from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import json
import re

from fastapi.middleware.cors import CORSMiddleware

from gemini_service import generate_text, generate_from_image
from firestore_service import save_document, get_document, list_documents

app = FastAPI(title="Backend API")

ALLOWED_ORIGINS = [
    "http://localhost:5173",       # Vite dev server
    "http://127.0.0.1:5173",
    # "https://<tuo-progetto>.web.app",       # <-- sostituisci con il tuo dominio Firebase Hosting
    # "https://<tuo-progetto>.firebaseapp.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


class GeminiRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gemini-2.5-flash"


class GeminiResponse(BaseModel):
    result: str


@app.post("/gemini/generate", response_model=GeminiResponse)
def gemini_generate(req: GeminiRequest):
    try:
        text = generate_text(req.prompt, req.model)
        return GeminiResponse(result=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DocumentIn(BaseModel):
    collection: str
    data: dict
    doc_id: Optional[str] = None


@app.post("/firestore/save")
def firestore_save(payload: DocumentIn):
    try:
        saved_id = save_document(payload.collection, payload.data, payload.doc_id)
        return {"id": saved_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/firestore/get/{collection}/{doc_id}")
def firestore_get(collection: str, doc_id: str):
    doc = get_document(collection, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return doc


@app.get("/firestore/list/{collection}")
def firestore_list(collection: str, limit: int = 50):
    return list_documents(collection, limit)


def _extract_json(raw_text: str) -> dict:
    """Ripulisce l'eventuale wrapping markdown (```json ... ```) e fa il parsing."""
    cleaned = raw_text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1)
    return json.loads(cleaned)


ANALYZE_PROMPT = """
Analizza il contenuto di questa pagina (libro, appunti, dispensa).

Restituisci ESCLUSIVAMENTE un JSON valido, senza testo aggiuntivo, con questa struttura esatta:

{
  "extractedText": "testo completo estratto dalla pagina",
  "concepts": ["concetto chiave 1", "concetto chiave 2", "..."],
  "questions": [
    {
      "type": "multipla",
      "question": "testo della domanda",
      "options": ["opzione A", "opzione B", "opzione C", "opzione D"],
      "correctAnswer": "opzione corretta"
    },
    {
      "type": "vero_falso",
      "question": "testo della domanda",
      "options": ["Vero", "Falso"],
      "correctAnswer": "Vero"
    },
    {
      "type": "aperta",
      "question": "testo della domanda",
      "options": null,
      "correctAnswer": "risposta attesa sintetica"
    }
  ]
}

Genera 5 domande totali, di difficoltà crescente (dal semplice richiamo di fatti fino
all'applicazione/comprensione), mescolando i tipi "multipla", "vero_falso" e "aperta".
Non aggiungere commenti, markdown o testo fuori dal JSON.
"""

EVALUATE_PROMPT = """
Domanda: {question}
Risposta corretta attesa: {correct_answer}
Risposta data dall'utente: {user_answer}

Valuta se la risposta dell'utente è corretta dal punto di vista del significato,
anche se non è formulata con le stesse parole della risposta attesa.

Restituisci ESCLUSIVAMENTE un JSON valido con questa struttura:

{{
  "isCorrect": true oppure false,
  "feedback": "breve spiegazione, massimo 2 frasi, in italiano"
}}

Non aggiungere altro testo oltre al JSON.
"""


@app.post("/analyze")
async def analyze(file: UploadFile = File(...), model: Optional[str] = Form("gemini-1.5-flash")):
    try:
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        raw_result = generate_from_image(
            ANALYZE_PROMPT,
            image_bytes,
            mime_type=mime_type,
            model=model,
        )
        
        # L'immagine non serve più: la scartiamo subito, non viene mai scritta su disco/storage
        del image_bytes

        parsed = _extract_json(raw_result)
        return parsed

    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Risposta del modello non in formato JSON valido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EvaluateRequest(BaseModel):
    question: str
    correctAnswer: str
    userAnswer: str
    model: Optional[str] = "gemini-1.5-flash"


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    try:
        prompt = EVALUATE_PROMPT.format(
            question=req.question,
            correct_answer=req.correctAnswer,
            user_answer=req.userAnswer,
        )
        raw_result = generate_text(prompt, req.model)
        parsed = _extract_json(raw_result)
        return parsed

    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Risposta del modello non in formato JSON valido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {
        "message": "Backend API is running",
        "health": "/health",
        "docs": "/docs"
    }
