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

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "backend-documental"

    # Claude API
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()