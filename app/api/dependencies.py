"""
Dependencias compartidas para los endpoints de la API
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infra.persistence.database import SessionLocal
from app.infra.repositories.profesional_repository import ProfesionalRepository
from app.infra.repositories.consulta_repository import ConsultaRepository
from app.infra.repositories.paciente_repository import PacienteRepository
from app.infra.repositories.valoracion_repository import ValoracionRepository
from app.infra.repositories.usuario_repository import UsuarioRepository
from app.infra.repositories.direccion_repository import DireccionRepository
from app.infra.repositories.catalogo_repository import CatalogoRepository
from app.services.auth_service import AuthService
from app.api.policies import IntegrityPolicies
from app.api.exceptions import ForbiddenException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency que provee una sesión de base de datos.
    Se cierra automáticamente al finalizar el request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_profesional_repository(
    db: Session = Depends(get_db),
) -> ProfesionalRepository:
    """Dependency para el repositorio de profesionales"""
    return ProfesionalRepository(db)


def get_consulta_repository(
    db: Session = Depends(get_db),
) -> ConsultaRepository:
    """Dependency para el repositorio de consultas"""
    return ConsultaRepository(db)


def get_paciente_repository(
    db: Session = Depends(get_db),
) -> PacienteRepository:
    """Dependency para el repositorio de pacientes"""
    return PacienteRepository(db)


def get_valoracion_repository(
    db: Session = Depends(get_db),
) -> ValoracionRepository:
    """Dependency para el repositorio de valoraciones"""
    return ValoracionRepository(db)


def get_direccion_repository(
    db: Session = Depends(get_db),
) -> DireccionRepository:
    """Dependency para el repositorio de direcciones"""
    return DireccionRepository(db)


def get_catalogo_repository(
    db: Session = Depends(get_db),
) -> CatalogoRepository:
    """Dependency para el repositorio de catálogo (especialidades, publicaciones)"""
    return CatalogoRepository(db)


def get_integrity_policies():
    """Dependency para acceder a las políticas de integridad"""
    return IntegrityPolicies


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Obtiene el usuario autenticado desde el JWT token.

    Returns:
        Usuario ORM entity

    Raises:
        HTTPException 401: Si el token es inválido o el usuario no existe
    """
    auth_service = AuthService(db)

    payload = auth_service.validar_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin identificador de usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.obtener_por_id(user_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not getattr(usuario, "activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
        )

    return usuario


async def get_current_profesional(
    current_user=Depends(get_current_user),
):
    """
    Obtiene el usuario autenticado y verifica que sea profesional.

    Returns:
        Usuario ORM entity con es_profesional=True

    Raises:
        ForbiddenException: Si el usuario no es profesional
    """
    if not getattr(current_user, "es_profesional", False):
        raise ForbiddenException(
            "Se requiere ser profesional para acceder a este recurso"
        )

    return current_user


async def get_current_solicitante(
    current_user=Depends(get_current_user),
):
    """
    Obtiene el usuario autenticado y verifica que sea solicitante.

    Returns:
        Usuario ORM entity con es_solicitante=True

    Raises:
        ForbiddenException: Si el usuario no es solicitante
    """
    if not getattr(current_user, "es_solicitante", False):
        raise ForbiddenException(
            "Se requiere ser solicitante para acceder a este recurso"
        )

    return current_user
