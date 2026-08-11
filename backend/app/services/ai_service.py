from anthropic import Anthropic

from app.config import settings
from app.core.logging_config import logger

client = Anthropic(api_key=settings.anthropic_api_key)


def analyze_document(filename: str) -> str:
    """
    Envía metadata del documento a Claude para generar un análisis breve.
    Por ahora analizamos solo el nombre del archivo (metadata), ya que
    la lectura del contenido del PDF/DOCX se puede añadir después.
    """
    prompt = f"""Eres un asistente de análisis documental para un sistema LegalTech.
Se ha recibido un documento con el siguiente nombre de archivo: "{filename}".

Basándote únicamente en el nombre del archivo, genera un análisis breve (máximo 3 líneas) que incluya:
1. Una hipótesis del tipo de documento que podría ser.
2. Una recomendación general de qué debería revisar el equipo legal antes de aprobarlo.

Responde en español, de forma concisa y profesional."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        result = message.content[0].text

        logger.info(
            "Análisis de IA generado exitosamente",
            extra={"extra_data": {"event": "ai_analysis_success", "filename": filename}},
        )

        return result

    except Exception as e:
        logger.error(
            "Error al generar análisis de IA",
            extra={"extra_data": {"event": "ai_analysis_error", "filename": filename, "error": str(e)}},
        )
        raise

def detect_anomalies(documents_data: list) -> str:
    prompt = f"""Eres un analista de observabilidad documental. Aquí tienes datos de documentos procesados:

{documents_data}

Identifica anomalías (tiempos de revisión inusuales, patrones de rechazo repetido, cuellos de botella). Responde en español, 
máximo 5 líneas, formato de lista."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(
            "Error al detectar anomalías",
            extra={"extra_data": {"event": "ai_anomaly_error", "error": str(e)}},
        )
        raise