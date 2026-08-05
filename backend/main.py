from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from gemini_service import generate_text
from firestore_service import save_document, get_document, list_documents

app = FastAPI(title="Backend API")


@app.get("/health")
def health():
    return {"status": "ok"}


class GeminiRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gemini-1.5-flash"


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