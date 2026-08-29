import os
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.core.security import get_current_user, require_role
from app.core.database import get_session_for_year, SessionShard1, SessionShard2
from app.core.logging_config import logger
from app.core.document_states import DocumentStatus
from app.models.document import Document
from app.services.ai_service import analyze_document, detect_anomalies
from app.core.database import get_session_for_year, get_replica_session_for_year, SessionShard1, SessionShard2, SessionShard1Replica, SessionShard2Replica

router = APIRouter()

os.makedirs(settings.upload_dir, exist_ok=True)


class ReviewRequest(BaseModel):
    comment: Optional[str] = None


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    allowed_extensions = [".pdf", ".docx", ".doc"]
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        logger.warning(
            "Intento de subida con extensión no permitida",
            extra={"extra_data": {"event": "upload_rejected", "filename": file.filename, "user": current_user["username"]}},
        )
        raise HTTPException(status_code=400, detail=f"Extensión no permitida. Use: {allowed_extensions}")

    document_id = str(uuid.uuid4())
    saved_filename = f"{document_id}{file_extension}"
    saved_path = os.path.join(settings.upload_dir, saved_filename)

    with open(saved_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    uploaded_at = datetime.utcnow()
    db = get_session_for_year(uploaded_at.year)

    new_document = Document(
        id=document_id,
        original_filename=file.filename,
        stored_path=saved_path,
        status=DocumentStatus.RECIBIDO,
        uploaded_by=current_user["username"],
        uploaded_at=uploaded_at,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    result = _serialize_document(new_document)
    replica_db = get_replica_session_for_year(uploaded_at.year)
    replica_doc = Document(
        id=new_document.id, original_filename=new_document.original_filename,
        stored_path=new_document.stored_path, status=new_document.status,
        uploaded_by=new_document.uploaded_by, uploaded_at=new_document.uploaded_at,
    )
    replica_db.add(replica_doc)
    replica_db.commit()
    replica_db.close()
    db.close()

    logger.info(
        "Documento subido exitosamente",
        extra={"extra_data": {"event": "document_uploaded", "document_id": str(new_document.id), "filename": new_document.original_filename, "user": current_user["username"], "shard": "shard2" if uploaded_at.year >= settings.shard_year_threshold else "shard1"}},
    )

    return result


@router.get("/")
def list_documents(current_user: dict = Depends(get_current_user)):
    docs_shard1 = SessionShard1Replica().query(Document).all()
    docs_shard2 = SessionShard2Replica().query(Document).all()
    all_docs = docs_shard1 + docs_shard2
    all_docs.sort(key=lambda d: d.uploaded_at, reverse=True)
    return {"total": len(all_docs), "documents": [_serialize_document(d) for d in all_docs]}

    logger.info(
        "Consulta de listado de documentos",
        extra={"extra_data": {"event": "documents_listed", "total": len(all_docs), "user": current_user["username"]}},
    )

    return {"total": len(all_docs), "documents": [_serialize_document(d) for d in all_docs]}


@router.get("/insights/anomalies")
def get_anomalies(current_user: dict = Depends(get_current_user)):
    docs_shard1 = SessionShard1().query(Document).all()
    docs_shard2 = SessionShard2().query(Document).all()
    documents = docs_shard1 + docs_shard2
    data = [{"filename": d.original_filename, "status": d.status, "uploaded_at": d.uploaded_at.isoformat(), "reviewed_at": d.reviewed_at.isoformat() if d.reviewed_at else None} for d in documents]
    try:
        result = detect_anomalies(data)
    except Exception:
        raise HTTPException(status_code=502, detail="No se pudo generar el análisis de anomalías")
    return {"anomalies": result}


@router.get("/{document_id}")
def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    document, _ = _find_document(document_id, current_user)
    return _serialize_document(document)


@router.post("/{document_id}/start-review")
def start_review(document_id: str, current_user: dict = Depends(get_current_user)):
    document, db = _find_document(document_id, current_user)
    return _transition_status(document, DocumentStatus.EN_REVISION, current_user, db)


@router.post("/{document_id}/approve")
def approve_document(document_id: str, review: ReviewRequest, current_user: dict = Depends(require_role("admin_documental"))):
    document, db = _find_document(document_id, current_user)
    return _transition_status(document, DocumentStatus.APROBADO, current_user, db, review.comment)


@router.post("/{document_id}/reject")
def reject_document(document_id: str, review: ReviewRequest, current_user: dict = Depends(require_role("admin_documental"))):
    document, db = _find_document(document_id, current_user)
    return _transition_status(document, DocumentStatus.RECHAZADO, current_user, db, review.comment)


@router.post("/{document_id}/analyze")
def analyze_document_endpoint(document_id: str, current_user: dict = Depends(get_current_user)):
    document, db = _find_document(document_id, current_user)
    try:
        analysis_result = analyze_document(document.original_filename)
    except Exception:
        raise HTTPException(status_code=502, detail="No se pudo generar el análisis de IA en este momento")

    document.ai_analysis = analysis_result
    document.ai_analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(document)
    result = _serialize_document(document)
    db.close()
    return result


# ------------------ Funciones auxiliares ------------------

def _find_document(document_id: str, current_user: dict):
    """Busca el documento en shard1, si no está busca en shard2. Devuelve (documento, sesion_abierta)."""
    db1 = SessionShard1()
    doc = db1.query(Document).filter(Document.id == document_id).first()
    if doc:
        return doc, db1
    db1.close()

    db2 = SessionShard2()
    doc = db2.query(Document).filter(Document.id == document_id).first()
    if doc:
        return doc, db2
    db2.close()

    logger.warning(
        "Consulta de documento inexistente",
        extra={"extra_data": {"event": "document_not_found", "document_id": document_id, "user": current_user["username"]}},
    )
    raise HTTPException(status_code=404, detail="Documento no encontrado")


def _transition_status(document: Document, new_status: str, current_user: dict, db, comment: Optional[str] = None) -> dict:
    if not DocumentStatus.is_valid_transition(document.status, new_status):
        db.close()
        raise HTTPException(status_code=400, detail=f"No se puede pasar de '{document.status}' a '{new_status}'")

    previous_status = document.status
    document.status = new_status
    document.reviewed_by = current_user["username"]
    document.reviewed_at = datetime.utcnow()
    if comment:
        document.review_comment = comment

    db.commit()
    db.refresh(document)
    result = _serialize_document(document)
    replica_db = get_replica_session_for_year(document.uploaded_at.year)
    replica_doc = replica_db.query(Document).filter(Document.id == document.id).first()
    if replica_doc:
        replica_doc.status = document.status
        replica_doc.reviewed_by = document.reviewed_by
        replica_doc.reviewed_at = document.reviewed_at
        replica_doc.review_comment = document.review_comment
        replica_db.commit()
    replica_db.close()
    db.close()

    logger.info(
        "Estado de documento actualizado",
        extra={"extra_data": {"event": "document_status_changed", "document_id": str(document.id), "from_status": previous_status, "to_status": new_status, "user": current_user["username"]}},
    )

    return result


def _serialize_document(document: Document) -> dict:
    return {
        "id": str(document.id),
        "original_filename": document.original_filename,
        "status": document.status,
        "uploaded_by": document.uploaded_by,
        "uploaded_at": document.uploaded_at.isoformat(),
        "reviewed_by": document.reviewed_by,
        "reviewed_at": document.reviewed_at.isoformat() if document.reviewed_at else None,
        "review_comment": document.review_comment,
        "ai_analysis": document.ai_analysis,
        "ai_analyzed_at": document.ai_analyzed_at.isoformat() if document.ai_analyzed_at else None,
    }