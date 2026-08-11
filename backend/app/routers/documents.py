from app.services.ai_service import analyze_document
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.core.security import get_current_user, require_role
from app.core.database import get_db
from app.core.logging_config import logger
from app.core.document_states import DocumentStatus
from app.models.document import Document

from app.services.ai_service import analyze_document, detect_anomalies

router = APIRouter()

os.makedirs(settings.upload_dir, exist_ok=True)


class ReviewRequest(BaseModel):
    comment: Optional[str] = None


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_extensions = [".pdf", ".docx", ".doc"]
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        logger.warning(
            "Intento de subida con extensión no permitida",
            extra={"extra_data": {
                "event": "upload_rejected",
                "filename": file.filename,
                "user": current_user["username"],
            }},
        )
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {allowed_extensions}"
        )

    document_id = uuid.uuid4()
    saved_filename = f"{document_id}{file_extension}"
    saved_path = os.path.join(settings.upload_dir, saved_filename)

    with open(saved_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    new_document = Document(
        id=document_id,
        original_filename=file.filename,
        stored_path=saved_path,
        status=DocumentStatus.RECIBIDO,
        uploaded_by=current_user["username"],
        uploaded_at=datetime.utcnow(),
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    logger.info(
        "Documento subido exitosamente",
        extra={"extra_data": {
            "event": "document_uploaded",
            "document_id": str(new_document.id),
            "filename": new_document.original_filename,
            "user": current_user["username"],
        }},
    )

    return _serialize_document(new_document)


@router.get("/")
def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()

    logger.info(
        "Consulta de listado de documentos",
        extra={"extra_data": {
            "event": "documents_listed",
            "total": len(documents),
            "user": current_user["username"],
        }},
    )

    return {
        "total": len(documents),
        "documents": [_serialize_document(doc) for doc in documents],
    }

@router.get("/insights/anomalies")
def get_anomalies(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.query(Document).all()
    data = [
        {
            "filename": d.original_filename,
            "status": d.status,
            "uploaded_at": d.uploaded_at.isoformat(),
            "reviewed_at": d.reviewed_at.isoformat() if d.reviewed_at else None,
        }
        for d in documents
    ]
    try:
        result = detect_anomalies(data)
    except Exception:
        raise HTTPException(status_code=502, detail="No se pudo generar el análisis de anomalías")
    return {"anomalies": result}

@router.get("/{document_id}")
def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(document_id, db, current_user)
    return _serialize_document(document)


@router.post("/{document_id}/analyze")
def analyze_document_endpoint(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Envía el documento a Claude API para generar un análisis."""
    document = _get_document_or_404(document_id, db, current_user)

    try:
        analysis_result = analyze_document(document.original_filename)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="No se pudo generar el análisis de IA en este momento",
        )

    document.ai_analysis = analysis_result
    document.ai_analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(document)

    return _serialize_document(document)


@router.post("/{document_id}/start-review")
def start_review(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Transición: recibido -> en_revision"""
    document = _get_document_or_404(document_id, db, current_user)
    return _transition_status(
        document, DocumentStatus.EN_REVISION, current_user, db
    )


@router.post("/{document_id}/approve")
def approve_document(
    document_id: str,
    review: ReviewRequest,
    current_user: dict = Depends(require_role("admin_documental")),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(document_id, db, current_user)
    return _transition_status(document, DocumentStatus.APROBADO, current_user, db, review.comment)


@router.post("/{document_id}/reject")
def reject_document(
    document_id: str,
    review: ReviewRequest,
    current_user: dict = Depends(require_role("admin_documental")),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(document_id, db, current_user)
    return _transition_status(document, DocumentStatus.RECHAZADO, current_user, db, review.comment)

# ------------------ Funciones auxiliares ------------------

def _get_document_or_404(document_id: str, db: Session, current_user: dict) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        logger.warning(
            "Consulta de documento inexistente",
            extra={"extra_data": {
                "event": "document_not_found",
                "document_id": document_id,
                "user": current_user["username"],
            }},
        )
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return document


def _transition_status(
    document: Document,
    new_status: str,
    current_user: dict,
    db: Session,
    comment: Optional[str] = None,
) -> dict:
    if not DocumentStatus.is_valid_transition(document.status, new_status):
        logger.warning(
            "Transición de estado inválida",
            extra={"extra_data": {
                "event": "invalid_status_transition",
                "document_id": str(document.id),
                "from_status": document.status,
                "to_status": new_status,
                "user": current_user["username"],
            }},
        )
        raise HTTPException(
            status_code=400,
            detail=f"No se puede pasar de '{document.status}' a '{new_status}'",
        )

    previous_status = document.status
    document.status = new_status
    document.reviewed_by = current_user["username"]
    document.reviewed_at = datetime.utcnow()
    if comment:
        document.review_comment = comment

    db.commit()
    db.refresh(document)

    logger.info(
        "Estado de documento actualizado",
        extra={"extra_data": {
            "event": "document_status_changed",
            "document_id": str(document.id),
            "from_status": previous_status,
            "to_status": new_status,
            "user": current_user["username"],
        }},
    )

    return _serialize_document(document)


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