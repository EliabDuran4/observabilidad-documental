class DocumentStatus:
    RECIBIDO = "recibido"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"

    # Transiciones válidas: desde qué estado se puede pasar a cuál
    TRANSITIONS = {
        RECIBIDO: [EN_REVISION],
        EN_REVISION: [APROBADO, RECHAZADO],
        APROBADO: [],
        RECHAZADO: [],
    }

    @classmethod
    def is_valid_transition(cls, current_status: str, new_status: str) -> bool:
        return new_status in cls.TRANSITIONS.get(current_status, [])