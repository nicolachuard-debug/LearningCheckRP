import json
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_SERVICE_ACCOUNT_JSON

_db = None

def get_db():
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        if FIREBASE_SERVICE_ACCOUNT_JSON:
            cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON non impostata: impossibile inizializzare Firebase."
            )

    _db = firestore.client()
    return _db


def save_document(collection: str, data: dict, doc_id: str = None):
    db = get_db()
    if doc_id:
        ref = db.collection(collection).document(doc_id)
        ref.set(data)
        return doc_id
    else:
        ref = db.collection(collection).document()
        ref.set(data)
        return ref.id


def get_document(collection: str, doc_id: str):
    db = get_db()
    doc = db.collection(collection).document(doc_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def list_documents(collection: str, limit: int = 50):
    db = get_db()
    docs = db.collection(collection).limit(limit).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]