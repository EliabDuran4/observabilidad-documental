from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Sistema de Observabilidad Documental"
    environment: str = "development"
    upload_dir: str = "uploads"

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "observabilidad-documental"
    keycloak_client_id: str = "sistema-documental-app"
    keycloak_client_secret: str = ""

    # Base de datos
    database_url: str = "postgresql+pg8000://admin:admin123@localhost:5433/observabilidad_documental_db"

    class Config:
        env_file = ".env"


settings = Settings()