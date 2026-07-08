from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.domain.entities.valoraciones import Valoracion
from app.infra.persistence.valoraciones import ValoracionORM


class ValoracionRepository:
    """
    Repositorio para gestionar la persistencia de Valoraciones.
    Implementa el patrón Repository para abstraer el acceso a datos.
    """

    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, orm: ValoracionORM) -> Valoracion:
        """
        Convierte un modelo ORM a entidad de dominio.

        Args:
            orm: Modelo ORM de la valoración

        Returns:
            Entidad Valoracion del dominio
        """
        return Valoracion(
            id=orm.id,
            id_profesional=orm.profesional_id,
            id_paciente=orm.paciente_id,
            puntuacion=orm.puntuacion,
            comentario=orm.comentario,
            fecha=orm.creado_en,
        )

    def _to_orm(
        self, valoracion: Valoracion, orm: ValoracionORM = None
    ) -> ValoracionORM:
        """
        Convierte una entidad de dominio a modelo ORM.

        Args:
            valoracion: Entidad Valoracion del dominio
            orm: Modelo ORM existente (para actualización)

        Returns:
            Modelo ORM de la valoración
        """
        if orm is None:
            orm = ValoracionORM(
                id=valoracion.id,
                profesional_id=valoracion.id_profesional,
                paciente_id=valoracion.id_paciente,
                puntuacion=valoracion.puntuacion,
                comentario=valoracion.comentario,
            )
        else:
            orm.puntuacion = valoracion.puntuacion
            orm.comentario = valoracion.comentario

        return orm

    def obtener_por_id(self, id: UUID) -> Optional[Valoracion]:
        """
        Obtiene una valoración por su ID.

        Args:
            id: UUID de la valoración

        Returns:
            Valoracion o None si no existe
        """
        orm = self.session.query(ValoracionORM).filter(ValoracionORM.id == id).first()

        return self._to_domain(orm) if orm else None

    def listar_por_profesional(
        self, profesional_id: UUID, limite: int = 100
    ) -> List[Valoracion]:
        """
        Lista las valoraciones de un profesional.

        Args:
            profesional_id: UUID del profesional
            limite: Número máximo de valoraciones a retornar

        Returns:
            Lista de valoraciones ordenadas por fecha descendente
        """
        orms = (
            self.session.query(ValoracionORM)
            .filter(ValoracionORM.profesional_id == profesional_id)
            .order_by(ValoracionORM.creado_en.desc())
            .limit(limite)
            .all()
        )

        return [self._to_domain(orm) for orm in orms]

    def listar_por_paciente(
        self, paciente_id: UUID, limite: int = 100
    ) -> List[Valoracion]:
        """
        Lista las valoraciones hechas por un paciente.

        Args:
            paciente_id: UUID del paciente
            limite: Número máximo de valoraciones a retornar

        Returns:
            Lista de valoraciones ordenadas por fecha descendente
        """
        orms = (
            self.session.query(ValoracionORM)
            .filter(ValoracionORM.paciente_id == paciente_id)
            .order_by(ValoracionORM.creado_en.desc())
            .limit(limite)
            .all()
        )

        return [self._to_domain(orm) for orm in orms]

    def obtener_promedio_profesional(self, profesional_id: UUID) -> float:
        """
        Calcula el promedio de valoraciones de un profesional.

        Args:
            profesional_id: UUID del profesional

        Returns:
            Promedio de puntuaciones (0.0 si no hay valoraciones)
        """
        from sqlalchemy import func

        resultado = (
            self.session.query(func.avg(ValoracionORM.puntuacion))
            .filter(ValoracionORM.profesional_id == profesional_id)
            .scalar()
        )

        return float(resultado) if resultado else 0.0

    def contar_por_profesional(self, profesional_id: UUID) -> int:
        """
        Cuenta el número de valoraciones de un profesional.

        Args:
            profesional_id: UUID del profesional

        Returns:
            Número total de valoraciones
        """
        return (
            self.session.query(ValoracionORM)
            .filter(ValoracionORM.profesional_id == profesional_id)
            .count()
        )

    def crear(self, valoracion: Valoracion) -> Valoracion:
        """
        Crea una nueva valoración en la base de datos.

        Args:
            valoracion: Entidad Valoracion del dominio

        Returns:
            Valoracion creada con datos actualizados
        """
        orm = self._to_orm(valoracion)

        self.session.add(orm)
        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def actualizar(self, valoracion: Valoracion) -> Optional[Valoracion]:
        """
        Actualiza una valoración existente.

        Args:
            valoracion: Entidad Valoracion con datos actualizados

        Returns:
            Valoracion actualizada o None si no existe
        """
        orm = (
            self.session.query(ValoracionORM)
            .filter(ValoracionORM.id == valoracion.id)
            .first()
        )

        if not orm:
            return None

        orm = self._to_orm(valoracion, orm)

        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def eliminar(self, id: UUID) -> bool:
        """
        Elimina una valoración.

        Args:
            id: UUID de la valoración

        Returns:
            True si se eliminó, False si no existía
        """
        orm = self.session.query(ValoracionORM).filter(ValoracionORM.id == id).first()

        if not orm:
            return False

        self.session.delete(orm)
        self.session.commit()

        return True

    def existe_valoracion(self, profesional_id: UUID, paciente_id: UUID) -> bool:
        """
        Verifica si ya existe una valoración de un paciente para un profesional.

        Args:
            profesional_id: UUID del profesional
            paciente_id: UUID del paciente

        Returns:
            True si existe, False en caso contrario
        """
        return (
            self.session.query(ValoracionORM)
            .filter(
                ValoracionORM.profesional_id == profesional_id,
                ValoracionORM.paciente_id == paciente_id,
            )
            .first()
            is not None
        )
