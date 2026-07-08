"""
Repository para operaciones de autenticación y gestión de tokens.
"""

from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.infra.persistence.auth import RefreshTokenORM, AuditoriaLoginORM


class AuthRepository:
    """
    Repositorio para gestionar autenticación, tokens y auditoría.

    Implementa:
    - Crear y validar refresh tokens
    - Revocar tokens (logout individual y global)
    - Registrar intentos de login (auditoría)
    - Limpiar tokens expirados (mantenimiento)
    - Detectar intentos de fuerza bruta
    """

    def __init__(self, db: Session):
        self.db = db

    def crear_refresh_token(
        self,
        usuario_id: str,
        token: str,
        expira_en: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RefreshTokenORM:
        """
        Crea un nuevo refresh token para el usuario.

        Args:
            usuario_id: ID del usuario (UUID)
            token: Token encriptado
            expira_en: Fecha de expiración
            ip_address: IP del cliente (opcional)
            user_agent: User agent del navegador (opcional)

        Returns:
            RefreshTokenORM creado
        """
        refresh_token = RefreshTokenORM(
            usuario_id=usuario_id,
            token=token,
            expira_en=expira_en,
            revocado=False,
            ip_address=ip_address,
            user_agent=user_agent,
            creado_en=datetime.now(timezone.utc),
        )

        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token

    def obtener_refresh_token(self, token: str) -> Optional[RefreshTokenORM]:
        """
        Busca un refresh token por su valor.

        Args:
            token: Token a buscar

        Returns:
            RefreshTokenORM si existe y es válido, None en caso contrario

        Validaciones:
            - Token existe
            - No está revocado
            - No está expirado
        """
        refresh_token = (
            self.db.query(RefreshTokenORM)
            .filter(
                and_(
                    RefreshTokenORM.token == token,
                    not RefreshTokenORM.revocado,
                    RefreshTokenORM.expira_en > datetime.now(timezone.utc),
                )
            )
            .first()
        )

        return refresh_token

    def revocar_refresh_token(self, token: str) -> bool:
        """
        Revoca un refresh token (logout de una sesión).

        Args:
            token: Token a revocar

        Returns:
            True si se revocó exitosamente, False si no se encontró
        """
        refresh_token = (
            self.db.query(RefreshTokenORM)
            .filter(RefreshTokenORM.token == token)
            .first()
        )

        if not refresh_token:
            return False

        refresh_token.revocado = True
        self.db.commit()

        return True

    def revocar_todos_tokens_usuario(self, usuario_id: str) -> int:
        """
        Revoca todos los tokens de un usuario (logout de todas las sesiones).

        Args:
            usuario_id: ID del usuario (UUID)

        Returns:
            Cantidad de tokens revocados

        Uso: Cuando el usuario cambia contraseña o cierra todas las sesiones
        """
        cantidad = (
            self.db.query(RefreshTokenORM)
            .filter(
                and_(
                    RefreshTokenORM.usuario_id == usuario_id,
                    not RefreshTokenORM.revocado,
                )
            )
            .update({"revocado": True})
        )

        self.db.commit()

        return cantidad

    def limpiar_tokens_expirados(self) -> int:
        """
        Elimina tokens expirados de la DB (tarea de mantenimiento).

        Returns:
            Cantidad de tokens eliminados

        Uso: Ejecutar periódicamente (ej: cron job diario)
        """
        cantidad = (
            self.db.query(RefreshTokenORM)
            .filter(RefreshTokenORM.expira_en < datetime.now(timezone.utc))
            .delete()
        )

        self.db.commit()

        return cantidad

    def registrar_intento_login(
        self,
        email: str,
        exitoso: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        motivo: Optional[str] = None,
    ) -> AuditoriaLoginORM:
        """
        Registra un intento de login en la tabla de auditoría.

        Args:
            email: Email del usuario que intentó hacer login
            exitoso: True si el login fue exitoso, False si falló
            ip_address: IP del cliente (opcional)
            user_agent: User agent del navegador (opcional)
            motivo: Razón del fallo (ej: "Contraseña incorrecta", "Usuario no existe")

        Returns:
            AuditoriaLoginORM creado
        """
        auditoria = AuditoriaLoginORM(
            email=email,
            exitoso=exitoso,
            ip_address=ip_address,
            user_agent=user_agent,
            motivo=motivo,
            fecha=datetime.now(timezone.utc),
        )

        self.db.add(auditoria)
        self.db.commit()
        self.db.refresh(auditoria)

        return auditoria

    def obtener_intentos_fallidos_recientes(self, email: str, minutos: int = 15) -> int:
        """
        Cuenta intentos de login fallidos en los últimos X minutos.

        Args:
            email: Email del usuario
            minutos: Ventana de tiempo a considerar (default: 15 minutos)

        Returns:
            Cantidad de intentos fallidos

        Uso: Detectar ataques de fuerza bruta y bloquear temporalmente
        """
        tiempo_limite = datetime.now(timezone.utc) - timedelta(minutes=minutos)

        cantidad = (
            self.db.query(AuditoriaLoginORM)
            .filter(
                and_(
                    AuditoriaLoginORM.email == email,
                    not AuditoriaLoginORM.exitoso,
                    AuditoriaLoginORM.fecha >= tiempo_limite,
                )
            )
            .count()
        )

        return cantidad
