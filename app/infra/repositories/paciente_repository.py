from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.entities.usuarios import Paciente
from app.domain.value_objects.objetos_valor import Ubicacion
from app.infra.persistence.paciente import PacienteORM
from app.infra.persistence.relaciones import RelacionSolicitanteORM
from app.infra.repositories.direccion_repository import DireccionRepository


class PacienteRepository:
    """
    Repositorio para gestionar la persistencia de Pacientes.
    Implementa el patrón Repository para abstraer el acceso a datos.
    """

    def __init__(self, session: Session):
        self.session = session
        self.direccion_repo = DireccionRepository(session)

    def _to_domain(self, orm: PacienteORM) -> Paciente:
        """
        Convierte un modelo ORM a entidad de dominio.

        Args:
            orm: Modelo ORM del paciente

        Returns:
            Entidad Paciente del dominio
        """
        # NOTA: Paciente NO tiene dirección propia
        # La ubicación del servicio es siempre la del SOLICITANTE
        # Por lo tanto, devolvemos ubicación vacía (no es relevante para el paciente)
        ubicacion = Ubicacion(
            provincia="", departamento="", barrio="", calle="", numero=""
        )

        return Paciente(
            id=orm.id,
            nombre=orm.nombre,
            apellido=orm.apellido,
            ubicacion=ubicacion,
            solicitante_id=orm.solicitante_id,
            relacion=orm.relacion.nombre if orm.relacion else "Yo mismo",
            fecha_nacimiento=orm.fecha_nacimiento or date(2000, 1, 1),
            notas=orm.notas or "",
        )

    def _to_orm(
        self, paciente: Paciente, solicitante_id: UUID, orm: PacienteORM = None
    ) -> PacienteORM:
        """
        Convierte una entidad de dominio a modelo ORM.

        Args:
            paciente: Entidad Paciente del dominio
            solicitante_id: UUID del solicitante responsable
            orm: Modelo ORM existente (para actualización)

        Returns:
            Modelo ORM del paciente
        """
        # Buscar el ID de la relación por nombre
        relacion_orm = (
            self.session.query(RelacionSolicitanteORM)
            .filter(RelacionSolicitanteORM.nombre.ilike(paciente.relacion))
            .first()
        )

        # Si no se encuentra la relación, usar "Yo mismo" (id=1) por defecto
        if not relacion_orm:
            relacion_orm = (
                self.session.query(RelacionSolicitanteORM)
                .filter(RelacionSolicitanteORM.nombre == "Yo mismo")
                .first()
            )

        relacion_id = relacion_orm.id if relacion_orm else 1

        if orm is None:
            orm = PacienteORM(
                id=paciente.id,
                nombre=paciente.nombre,
                apellido=paciente.apellido,
                fecha_nacimiento=paciente.fecha_nacimiento,
                notas=paciente.notas,
                solicitante_id=solicitante_id,
                relacion_id=relacion_id,
            )
        else:
            orm.nombre = paciente.nombre
            orm.apellido = paciente.apellido
            orm.fecha_nacimiento = paciente.fecha_nacimiento
            orm.notas = paciente.notas
            orm.relacion_id = relacion_id

        return orm

    def obtener_por_id(self, id: UUID) -> Optional[Paciente]:
        """
        Obtiene un paciente por su ID.

        Args:
            id: UUID del paciente

        Returns:
            Paciente o None si no existe
        """
        orm = self.session.query(PacienteORM).filter(PacienteORM.id == id).first()

        return self._to_domain(orm) if orm else None

    def listar_todos(self, limite: int = 100) -> List[Paciente]:
        """
        Lista todos los pacientes.

        Args:
            limite: Número máximo de pacientes a retornar

        Returns:
            Lista de pacientes
        """
        orms = self.session.query(PacienteORM).limit(limite).all()
        return [self._to_domain(orm) for orm in orms]

    def listar_por_solicitante(self, solicitante_id: UUID) -> List[Paciente]:
        """
        Lista los pacientes de un solicitante.

        Args:
            solicitante_id: UUID del solicitante

        Returns:
            Lista de pacientes
        """
        orms = (
            self.session.query(PacienteORM)
            .filter(PacienteORM.solicitante_id == solicitante_id)
            .all()
        )

        return [self._to_domain(orm) for orm in orms]

    def buscar_por_nombre(self, nombre: str, apellido: str = None) -> List[Paciente]:
        """
        Busca pacientes por nombre y opcionalmente por apellido.

        Args:
            nombre: Nombre del paciente
            apellido: Apellido del paciente (opcional)

        Returns:
            Lista de pacientes que coinciden
        """
        query = self.session.query(PacienteORM).filter(
            PacienteORM.nombre.ilike(f"%{nombre}%")
        )

        if apellido:
            query = query.filter(PacienteORM.apellido.ilike(f"%{apellido}%"))

        orms = query.all()
        return [self._to_domain(orm) for orm in orms]

    def crear(self, paciente: Paciente, solicitante_id: UUID) -> Paciente:
        """
        Crea un nuevo paciente en la base de datos.

        Args:
            paciente: Entidad Paciente del dominio
            solicitante_id: UUID del solicitante responsable

        Returns:
            Paciente creado con datos actualizados

        Note:
            Paciente NO tiene dirección propia.
            La ubicación del servicio es la del SOLICITANTE.
        """
        orm = self._to_orm(paciente, solicitante_id)

        self.session.add(orm)
        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def actualizar(self, paciente: Paciente) -> Optional[Paciente]:
        """
        Actualiza un paciente existente.

        Args:
            paciente: Entidad Paciente con datos actualizados

        Returns:
            Paciente actualizado o None si no existe

        Note:
            Paciente NO tiene dirección propia.
            La ubicación del servicio es la del SOLICITANTE.
        """
        orm = (
            self.session.query(PacienteORM)
            .filter(PacienteORM.id == paciente.id)
            .first()
        )

        if not orm:
            return None

        orm = self._to_orm(paciente, orm.solicitante_id, orm)

        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def eliminar(self, id: UUID) -> bool:
        """
        Elimina un paciente (hard delete).

        Args:
            id: UUID del paciente

        Returns:
            True si se eliminó, False si no existía
        """
        orm = self.session.query(PacienteORM).filter(PacienteORM.id == id).first()

        if not orm:
            return False

        self.session.delete(orm)
        self.session.commit()
        return True

    def contar_pacientes(self, solicitante_id: UUID = None) -> int:
        """
        Cuenta el número de pacientes.

        Args:
            solicitante_id: Si se especifica, cuenta solo los pacientes de ese solicitante

        Returns:
            Número de pacientes
        """
        query = self.session.query(PacienteORM)

        if solicitante_id:
            query = query.filter(PacienteORM.solicitante_id == solicitante_id)

        return query.count()
