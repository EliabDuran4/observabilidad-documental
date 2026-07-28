import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.core.logging_config import logger

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(credentials: LoginRequest):
    """
    Autentica al usuario contra Keycloak y devuelve el token JWT.
    """
    token_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"

    data = {
        "grant_type": "password",
        "client_id": settings.keycloak_client_id,
        "client_secret": settings.keycloak_client_secret,
        "username": credentials.username,
        "password": credentials.password,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)

    if response.status_code != 200:
        logger.warning(
            "Intento de login fallido",
            extra={"extra_data": {"event": "login_failed", "username": credentials.username}},
        )
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    logger.info(
        "Login exitoso",
        extra={"extra_data": {"event": "login_success", "username": credentials.username}},
    )

    return response.json()