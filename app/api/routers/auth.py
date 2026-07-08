"""
Router de autenticación real (MVP): registro, login, me, refresh y logout con JWT.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel

from app.api.schemas import TokenSchema, LoginRequest, RegisterRequest
from app.api.dependencies import get_db
from app.services.auth_service import AuthService
from app.infra.repositories.usuario_repository import UsuarioRepository

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


class RefreshTokenRequest(BaseModel):
    """Schema para solicitar un nuevo access token"""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Schema para cerrar sesión"""

    refresh_token: str


@router.post("/register-json", status_code=status.HTTP_201_CREATED)
def registrar_usuario(data: RegisterRequest, db=Depends(get_db)):
    """Crea un usuario nuevo y devuelve sus datos básicos (sin password)."""
    svc = AuthService(db)
    try:
        creado = svc.registrar_usuario(
            email=data.email,
            password=data.password,
            nombre=data.nombre,
            apellido=data.apellido,
            celular=data.celular,
            es_profesional=data.es_profesional,
            es_solicitante=data.es_solicitante,
        )
        return creado
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/login", response_model=TokenSchema)
def login(creds: LoginRequest, db=Depends(get_db)):
    """Autentica con email/password y devuelve un access_token (bearer)."""
    svc = AuthService(db)
    try:
        return svc.login(email=creds.email, password=creds.password)
    except PermissionError as pe:
        raise HTTPException(status_code=423, detail=str(pe))
    except ValueError:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")


@router.get("/me")
def obtener_usuario_actual(
    authorization: Optional[str] = Header(default=None),
    db=Depends(get_db),
):
    """Decodifica el token Bearer y devuelve el perfil básico del usuario."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    token = authorization.split(" ", 1)[1]
    svc = AuthService(db)
    payload = svc.validar_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token sin 'sub'")

    repo = UsuarioRepository(db)
    user = repo.obtener_por_id(sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "id": str(user.id),
        "email": user.email,
        "nombre": user.nombre,
        "apellido": user.apellido,
        "roles": [
            r
            for r, active in (
                ("profesional", bool(getattr(user, "es_profesional", False))),
                ("solicitante", bool(getattr(user, "es_solicitante", False))),
            )
            if active
        ],
        "activo": bool(getattr(user, "activo", True)),
        "verificado": bool(getattr(user, "verificado", False)),
        "ultimo_login": getattr(user, "ultimo_login", None),
    }


@router.post("/refresh", response_model=TokenSchema)
def refresh_token(data: RefreshTokenRequest, db=Depends(get_db)):
    """
    Genera un nuevo access token usando un refresh token válido.

    El refresh token se obtiene en el login y tiene mayor duración (30 días).
    """
    svc = AuthService(db)
    try:
        return svc.refresh_access_token(data.refresh_token)
    except ValueError as ve:
        raise HTTPException(status_code=401, detail=str(ve))


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(data: LogoutRequest, db=Depends(get_db)):
    """
    Cierra la sesión revocando el refresh token.

    Después de esto, el refresh token ya no podrá usarse para obtener
    nuevos access tokens.
    """
    svc = AuthService(db)
    revocado = svc.logout(data.refresh_token)

    if not revocado:
        raise HTTPException(status_code=404, detail="Refresh token no encontrado")

    return {"message": "Sesión cerrada exitosamente"}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
def logout_all(authorization: Optional[str] = Header(default=None), db=Depends(get_db)):
    """
    Cierra todas las sesiones del usuario actual.

    Revoca todos los refresh tokens, forzando logout en todos los dispositivos.
    Requiere un access token válido.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")

    token = authorization.split(" ", 1)[1]
    svc = AuthService(db)
    payload = svc.validar_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Token sin 'sub'")

    cantidad = svc.logout_all(usuario_id)

    return {
        "message": f"Cerradas {cantidad} sesiones",
        "sesiones_cerradas": cantidad,
    }
