from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.document import Document
from app.services.parsing import extract_text

router = APIRouter(prefix="/documents", tags=["documents"])
VALID_KINDS = {"transcript", "syllabus", "job"}


@router.post("")
async def upload_document(
    kind: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if kind not in VALID_KINDS:
        raise HTTPException(400, f"kind must be one of {sorted(VALID_KINDS)}")

    data = await file.read()
    try:
        text = extract_text(file.filename, data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not text:
        raise HTTPException(422, "No readable text found. Is this a scanned PDF?")

    # Same document uploaded again? Reuse it, so earlier AI results can be reused too.
    existing = db.query(Document).filter(Document.kind == kind, Document.text == text).first()
    if existing:
        doc = existing
    else:
        doc = Document(kind=kind, filename=file.filename, text=text)
        db.add(doc)
        db.commit()
        db.refresh(doc)

    return {
        "id": doc.id,
        "kind": doc.kind,
        "filename": doc.filename,
        "chars": len(text),
        "preview": text[:300],
        "reused": existing is not None,
    }


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return {"id": doc.id, "kind": doc.kind, "filename": doc.filename, "text": doc.text}


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.id.desc()).all()
    return [{"id": d.id, "kind": d.kind, "filename": d.filename} for d in docs]
