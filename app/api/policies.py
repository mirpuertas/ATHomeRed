"""
Policies de integridad de negocio
Validaciones que garantizan la consistencia de la lógica de dominio
"""

from uuid import UUID
from sqlalchemy.orm import Session
from app.infra.persistence.usuarios import UsuarioORM
from app.infra.persistence.paciente import PacienteORM
from app.infra.persistence.perfiles import ProfesionalORM, SolicitanteORM
from app.api.exceptions import (
    ResourceNotFoundException,
    ForbiddenException,
)
from sqlalchemy import select


class IntegrityPolicies:
    """Policies de integridad para validar reglas de negocio"""

    @staticmethod
    def validar_usuario_activo(session: Session, usuario_id: UUID) -> UsuarioORM:
        """
        Policy 1: Solo usuarios ACTIVOS pueden operar en el sistema

        Raises:
            ForbiddenException: Si el usuario está inactivo
            ResourceNotFoundException: Si el usuario no existe
        """
        # NOTA IMPORTANTE SQLAlchemy 2.x:
        # Cuando existen relaciones con cargas "joined" sobre colecciones,
        # el Result puede tener filas duplicadas para la misma entidad.
        # Por eso usamos `.unique()` antes de `scalar_one_or_none()`.
        usuario = (
            session.execute(select(UsuarioORM).where(UsuarioORM.id == usuario_id))
            .unique()
            .scalar_one_or_none()
        )

        if not usuario:
            raise ResourceNotFoundException(f"Usuario {usuario_id} no encontrado")

        if not usuario.activo:
            raise ForbiddenException(f"Usuario {usuario_id} está inactivo")

        return usuario

    @staticmethod
    def validar_profesional_disponible(
        session: Session, profesional_id: UUID
    ) -> ProfesionalORM:
        """
        Policy 2: Solo profesionales VERIFICADOS y ACTIVOS pueden tener citas

        Raises:
            ResourceNotFoundException: Si el profesional no existe
            ForbiddenException: Si no está activo o verificado
        """
        # ProfesionalORM tiene relaciones con cargas "joined" (por ejemplo,
        # `especialidades` con `lazy="joined"`). En SQLAlchemy 2.x esto obliga
        # a llamar a `.unique()` sobre el Result antes de usar `scalar*()`.
        profesional = (
            session.execute(
                select(ProfesionalORM).where(ProfesionalORM.id == profesional_id)
            )
            .unique()
            .scalar_one_or_none()
        )

        if not profesional:
            raise ResourceNotFoundException(
                f"Profesional {profesional_id} no encontrado"
            )

        if not profesional.activo:
            raise ForbiddenException(f"Profesional {profesional_id} no está activo")

        if not profesional.verificado:
            raise ForbiddenException(f"Profesional {profesional_id} no está verificado")

        return profesional

    @staticmethod
    def validar_solicitante_es_dueno(
        session: Session, paciente_id: UUID, solicitante_id: UUID
    ) -> PacienteORM:
        """
        Policy 3: Solo el solicitante DUEÑO del paciente puede crear citas para ese paciente.

        IMPORTANTE:
        - `solicitante_id` se interpreta como el ID de `UsuarioORM` (usuario autenticado).
        - En base de datos, la relación es: UsuarioORM → SolicitanteORM → PacienteORM.
          Por eso validamos que el paciente indicado esté asociado a un SolicitanteORM
          cuyo `usuario_id` coincida con el `solicitante_id` recibido.

        Validación de permisos: Solicitante → Paciente (1-a-1)

        Raises:
            ResourceNotFoundException: Si el paciente no existe
            ForbiddenException: Si el solicitante no es el dueño del paciente
        """
        paciente = (
            session.execute(
                select(PacienteORM)
                .join(SolicitanteORM, PacienteORM.solicitante_id == SolicitanteORM.id)
                .where(
                    PacienteORM.id == paciente_id,
                    SolicitanteORM.usuario_id == solicitante_id,
                )
            )
            .unique()
            .scalar_one_or_none()
        )

        if not paciente:
            # Puede ser que el paciente no exista o que no pertenezca al solicitante
            raise ForbiddenException(
                f"Solicitante {solicitante_id} no es el dueño del paciente {paciente_id}"
            )

        return paciente

    @staticmethod
    def validar_paciente_existe(session: Session, paciente_id: UUID) -> PacienteORM:
        """Valida que un paciente existe (sin policy de permisos)"""
        paciente = (
            session.execute(select(PacienteORM).where(PacienteORM.id == paciente_id))
            .unique()
            .scalar_one_or_none()
        )

        if not paciente:
            raise ResourceNotFoundException(f"Paciente {paciente_id} no encontrado")

        return paciente
