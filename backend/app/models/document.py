import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="recibido")
    uploaded_by = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(String, nullable=True)

    # Nuevo: resultado del análisis de IA
    ai_analysis = Column(Text, nullable=True)
    ai_analyzed_at = Column(DateTime, nullable=True)