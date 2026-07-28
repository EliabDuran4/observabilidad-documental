import logging
import json
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Formatea los logs como JSON estructurado, ideal para observabilidad."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Agrega campos extra si existen (ej. usuario, documento, etc.)
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging():
    logger = logging.getLogger("observabilidad_documental")
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers si se llama más de una vez
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()