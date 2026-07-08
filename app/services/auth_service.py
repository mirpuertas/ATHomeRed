"""
Servicio de autenticación: lógica de negocio mínima pero funcional.

- Hasheamos contraseñas con Argon2 y verificamos con passlib.
- Armamos y validamos JWTs (HS256) para sesiones cortas.
- Registramos usuarios y manejamos el login con control de intentos fallidos.
- Implementa refresh tokens y auditoría de login.
"""

from typing import Optional
from datetime import datetime, timedelta, timezone
import os
import secrets

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.infra.repositories.usuario_repository import UsuarioRepository
from app.infra.repositories.auth_repository import AuthRepository

ALGORITHM = "HS256"

SECRET_KEY = os.getenv("AT_HOME_RED_SECRET", "dev-secret-change-me")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService:
    """Encapsulamos la lógica de autenticación en un servicio."""

    def __init__(self, db: Session):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)
        self.auth_repo = AuthRepository(db)

    @staticmethod
    def hash_password(password: str) -> str:
        """Devolvemos el hash Argon2 de la contraseña."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificamos si la contraseña en texto coincide con el hash Argon2."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    @staticmethod
    def crear_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Creamos un JWT con expiración usando SECRET_KEY y HS256.

        `data` suele traer: {"sub": user_id, "email": email, "roles": [...]}"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    def validar_access_token(token: str) -> Optional[dict]:
        """Decodificamos el JWT y devolvemos el payload, o None si no va."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if not payload.get("sub"):
                return None
            return payload
        except JWTError:
            return None

    def registrar_usuario(
        self,
        email: str,
        password: str,
        nombre: str,
        apellido: str,
        celular: Optional[str] = None,
        es_profesional: bool = False,
        es_solicitante: bool = True,
    ) -> dict:
        """Registramos un usuario nuevo y devolvemos datos básicos para la API/UI."""
        if es_profesional and es_solicitante:
            raise ValueError(
                "Un usuario no puede ser profesional y solicitante a la vez"
            )
        if not es_profesional and not es_solicitante:
            es_solicitante = True

        if self.usuario_repo.obtener_por_email(email):
            raise ValueError("El email ya está registrado")

        password_hash = self.hash_password(password)

        usuario = self.usuario_repo.crear_usuario(
            email=email,
            password_hash=password_hash,
            nombre=nombre,
            apellido=apellido,
            celular=celular,
            es_profesional=es_profesional,
            es_solicitante=es_solicitante,
        )

        return {
            "id": str(usuario.id),
            "usuario_id": str(usuario.id),
            "email": usuario.email,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "roles": [
                r
                for r, active in (
                    (
                        "profesional",
                        bool(getattr(usuario, "es_profesional", False)),
                    ),
                    (
                        "solicitante",
                        bool(getattr(usuario, "es_solicitante", False)),
                    ),
                )
                if active
            ],
        }

    def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Autenticamos y devolvemos {access_token, refresh_token, token_type}.

        También registra el intento en auditoría.
        """

        if self.usuario_repo.esta_bloqueado(email):
            self.auth_repo.registrar_intento_login(
                email=email,
                exitoso=False,
                ip_address=ip_address,
                user_agent=user_agent,
                motivo="Usuario bloqueado por intentos fallidos",
            )
            raise PermissionError(
                "Usuario temporalmente bloqueado por intentos fallidos. "
                "Intenta más tarde."
            )

        usuario = self.usuario_repo.obtener_por_email(email)
        if not usuario:
            self.usuario_repo.incrementar_intentos_fallidos(email)
            self.auth_repo.registrar_intento_login(
                email=email,
                exitoso=False,
                ip_address=ip_address,
                user_agent=user_agent,
                motivo="Usuario no existe",
            )
            raise ValueError("Credenciales inválidas")

        if not usuario.activo:
            self.auth_repo.registrar_intento_login(
                email=email,
                exitoso=False,
                ip_address=ip_address,
                user_agent=user_agent,
                motivo="Usuario inactivo",
            )
            raise ValueError("Usuario inactivo")

        if not usuario.password_hash or not self.verify_password(
            password, usuario.password_hash
        ):
            self.usuario_repo.incrementar_intentos_fallidos(email)
            self.auth_repo.registrar_intento_login(
                email=email,
                exitoso=False,
                ip_address=ip_address,
                user_agent=user_agent,
                motivo="Contraseña incorrecta",
            )
            raise ValueError("Credenciales inválidas")

        self.usuario_repo.resetear_intentos_fallidos(usuario.id)
        self.usuario_repo.actualizar_ultimo_login(usuario.id)

        self.auth_repo.registrar_intento_login(
            email=email,
            exitoso=True,
            ip_address=ip_address,
            user_agent=user_agent,
            motivo=None,
        )

        roles = []
        if getattr(usuario, "es_profesional", False):
            roles.append("profesional")
        if getattr(usuario, "es_solicitante", False):
            roles.append("solicitante")

        access_token = self.crear_access_token(
            data={
                "sub": str(usuario.id),
                "email": usuario.email,
                "roles": roles,
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        refresh_token_value = secrets.token_urlsafe(64)
        refresh_expira = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )

        self.auth_repo.crear_refresh_token(
            usuario_id=str(usuario.id),
            token=refresh_token_value,
            expira_en=refresh_expira,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_value,
            "token_type": "bearer",
        }

    def logout(self, refresh_token: str) -> bool:
        """
        Revoca un refresh token (logout de una sesión específica).

        Args:
            refresh_token: Token a revocar

        Returns:
            True si se revocó exitosamente
        """
        return self.auth_repo.revocar_refresh_token(refresh_token)

    def logout_all(self, usuario_id: str) -> int:
        """
        Cierra todas las sesiones de un usuario.

        Args:
            usuario_id: ID del usuario (UUID)

        Returns:
            Cantidad de sesiones cerradas
        """
        return self.auth_repo.revocar_todos_tokens_usuario(usuario_id)

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Genera un nuevo access token usando un refresh token válido.

        Args:
            refresh_token: Refresh token a validar

        Returns:
            dict con nuevo access_token

        Raises:
            ValueError si el token es inválido, expirado o revocado
        """
        token_orm = self.auth_repo.obtener_refresh_token(refresh_token)

        if not token_orm:
            raise ValueError("Refresh token inválido, expirado o revocado")

        usuario = self.usuario_repo.obtener_por_id(token_orm.usuario_id)

        if not usuario or not usuario.activo:
            raise ValueError("Usuario no encontrado o inactivo")

        roles = []
        if getattr(usuario, "es_profesional", False):
            roles.append("profesional")
        if getattr(usuario, "es_solicitante", False):
            roles.append("solicitante")

        access_token = self.crear_access_token(
            data={
                "sub": str(usuario.id),
                "email": usuario.email,
                "roles": roles,
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return {"access_token": access_token, "token_type": "bearer"}
