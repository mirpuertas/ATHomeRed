"""
Repository para operaciones CRUD de usuarios (autenticación).
"""

from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.infra.persistence.usuarios import UsuarioORM


class UsuarioRepository:
    """
    Repositorio para gestionar usuarios en el contexto de autenticación.

    Incluye métodos para:
    - CRUD de usuarios
    - Autenticación y login
    - Rate limiting (bloqueos por intentos fallidos)
    - Gestión de sesiones
    """

    def __init__(self, db: Session):
        self.db = db

    def crear_usuario(
        self,
        email: str,
        password_hash: str,
        nombre: str,
        apellido: str,
        celular: Optional[str] = None,
        es_profesional: bool = False,
        es_solicitante: bool = True,
    ) -> UsuarioORM:
        """
        Crea un nuevo usuario con contraseña hasheada.

        IMPORTANTE: NO hashear la password aquí, debe venir ya hasheada.
        """
        existente = self.obtener_por_email(email)
        if existente:
            raise ValueError("El email ya está registrado")

        usuario = UsuarioORM(
            email=email,
            password_hash=password_hash,
            nombre=nombre,
            apellido=apellido,
            celular=celular,
            es_profesional=es_profesional,
            es_solicitante=es_solicitante,
        )
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def obtener_por_email(self, email: str) -> Optional[UsuarioORM]:
        """
        Busca un usuario por su email.

        - Buscar usuario donde email = email
        - Retornar usuario o None
        """
        return self.db.query(UsuarioORM).filter(UsuarioORM.email == email).one_or_none()

    def obtener_por_id(self, usuario_id) -> Optional[UsuarioORM]:
        """
        Busca un usuario por su ID.

        - Buscar usuario por ID
        - Retornar usuario o None
        """

        try:
            return self.db.get(UsuarioORM, usuario_id)
        except Exception:
            return None

    def actualizar_password(self, usuario_id, nuevo_password_hash: str) -> bool:
        """
        Actualiza la contraseña de un usuario.

        - Buscar usuario por ID
        - Actualizar password_hash
        - Guardar cambios
        - Retornar True si exitoso
        """
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        usuario.password_hash = nuevo_password_hash
        self.db.commit()
        return True

    def actualizar_ultimo_login(self, usuario_id) -> bool:
        """
        Actualiza la fecha de último login.

        - Buscar usuario
        - Actualizar ultimo_login = datetime.utcnow()
        - Resetear intentos_fallidos = 0
        - Guardar cambios
        """
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        usuario.ultimo_login = datetime.now(timezone.utc)
        usuario.intentos_fallidos = 0
        self.db.commit()
        return True

    def incrementar_intentos_fallidos(self, email: str) -> int:
        """
        Incrementa el contador de intentos fallidos.

        - Buscar usuario por email
        - Incrementar intentos_fallidos
        - Si intentos >= 5, bloquear_hasta = now + 15 minutos
        - Guardar cambios
        - Retornar cantidad de intentos
        """
        usuario = self.obtener_por_email(email)
        if not usuario:
            return 0
        usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
        if usuario.intentos_fallidos >= 5:
            usuario.bloqueado_hasta = datetime.now(timezone.utc) + timedelta(minutes=15)
        self.db.commit()
        return usuario.intentos_fallidos

    def resetear_intentos_fallidos(self, usuario_id) -> bool:
        """
        Resetea el contador de intentos fallidos a 0.

        - Buscar usuario
        - intentos_fallidos = 0
        - bloqueado_hasta = None
        - Guardar cambios
        """
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        self.db.commit()
        return True

    def esta_bloqueado(self, email: str) -> bool:
        """
        Verifica si un usuario está bloqueado por intentos fallidos.

        - Buscar usuario por email
        - Si bloqueado_hasta es None: return False
        - Si bloqueado_hasta > datetime.utcnow(): return True
        - Si bloqueado_hasta <= datetime.utcnow(): desbloquear y return False
        """
        usuario = self.obtener_por_email(email)
        if not usuario:
            return False
        if not usuario.bloqueado_hasta:
            return False
        now = datetime.now(timezone.utc)
        if usuario.bloqueado_hasta > now:
            return True
        usuario.bloqueado_hasta = None
        usuario.intentos_fallidos = 0
        self.db.commit()
        return False

    def marcar_como_verificado(self, usuario_id) -> bool:
        """
        Marca un usuario como verificado (email confirmado).

        - Buscar usuario
        - verificado = True
        - Guardar cambios
        """
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        usuario.verificado = True
        self.db.commit()
        return True

    def activar_desactivar(self, usuario_id, activo: bool) -> bool:
        """
        Activa o desactiva un usuario.

        - Buscar usuario
        - activo = activo
        - Guardar cambios
        """
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        usuario.activo = bool(activo)
        self.db.commit()
        return True
