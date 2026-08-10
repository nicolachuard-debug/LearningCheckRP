import io
import os
import tempfile
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import magic  # optional, per rilevare MIME

app = FastAPI()

# Configurazioni minime
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_MIMES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}

def detect_mime(bytes) -> str:
    try:
        return magic.from_buffer(data, mime=True)
    except Exception:
        return ""

def ocr_image_pil(pil_image: Image.Image) -> str:
    pil_gray = pil_image.convert("L")
    return pytesseract.image_to_string(pil_gray)

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> dict:
    result = {"text": "", "images_extracted": 0, "ocr_pages": []}
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        page_text = page.get_text("text")
        if page_text and page_text.strip():
            result["text"] += page_text + "\n\n"
        else:
            # rasterize page to image and OCR
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = ocr_image_pil(img)
            result["text"] += ocr_text + "\n\n"
            result["ocr_pages"].append(page_index + 1)
        # optionally extract embedded images
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            # could save or process image_bytes here
            result["images_extracted"] += 1
    return result

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File vuoto")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File troppo grande")
    mime = detect_mime(contents) or file.content_type
    if mime not in ALLOWED_MIMES:
        raise HTTPException(status_code=415, detail=f"Tipo file non supportato: {mime}")

    if mime == "application/pdf" or file.filename.lower().endswith(".pdf"):
        try:
            pdf_result = extract_text_from_pdf_bytes(contents)
            return JSONResponse({
                "filename": file.filename,
                "mime": mime,
                "type": "pdf",
                "text": pdf_result["text"],
                "ocr_pages": pdf_result["ocr_pages"],
                "images_extracted": pdf_result["images_extracted"]
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore elaborazione PDF: {e}")

    # immagini singole
    try:
        img = Image.open(io.BytesIO(contents))
        text = ocr_image_pil(img)
        return JSONResponse({
            "filename": file.filename,
            "mime": mime,
            "type": "image",
            "text": text
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore elaborazione immagine: {e}")
