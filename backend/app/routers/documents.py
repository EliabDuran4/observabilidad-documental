import os
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_current_user
from app.core.database import get_db
from app.core.logging_config import logger
from app.models.document import Document

router = APIRouter()

os.makedirs(settings.upload_dir, exist_ok=True)


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
        status="recibido",
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

    return {
        "message": "Documento cargado exitosamente",
        "document": {
            "id": str(new_document.id),
            "original_filename": new_document.original_filename,
            "status": new_document.status,
            "uploaded_by": new_document.uploaded_by,
            "uploaded_at": new_document.uploaded_at.isoformat(),
        },
    }


@router.get("/")
def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.query(Document).all()

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
        "documents": [
            {
                "id": str(doc.id),
                "original_filename": doc.original_filename,
                "status": doc.status,
                "uploaded_by": doc.uploaded_by,
                "uploaded_at": doc.uploaded_at.isoformat(),
            }
            for doc in documents
        ],
    }


@router.get("/{document_id}")
def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    logger.info(
        "Consulta de documento individual",
        extra={"extra_data": {
            "event": "document_viewed",
            "document_id": document_id,
            "user": current_user["username"],
        }},
    )

    return {
        "id": str(document.id),
        "original_filename": document.original_filename,
        "status": document.status,
        "uploaded_by": document.uploaded_by,
        "uploaded_at": document.uploaded_at.isoformat(),
    }