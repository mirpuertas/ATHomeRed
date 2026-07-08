"""
Repositorio para gestionar el catálogo de especialidades, publicaciones y tarifas.

Responsabilidades:
- CRUD de especialidades
- Gestión de publicaciones de profesionales
- Consulta de tarifas vigentes
- Conversión entre entidades del dominio y modelos ORM
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date

from app.domain.entities.catalogo import Especialidad, Publicacion
from app.infra.persistence.servicios import EspecialidadORM
from app.infra.persistence.publicaciones import PublicacionORM


class CatalogoRepository:
    """
    Repositorio para gestionar especialidades, publicaciones y tarifas.

    Permite:
    - Listar y buscar especialidades
    - Crear y consultar publicaciones de profesionales
    - Obtener tarifas vigentes por especialidad
    """

    def __init__(self, session: Session):
        self.session = session

    def _especialidad_to_domain(self, orm: EspecialidadORM) -> Especialidad:
        """Convierte EspecialidadORM a Especialidad del dominio"""
        return Especialidad(
            id=orm.id_especialidad, nombre=orm.nombre, tarifa=orm.tarifa
        )

    def _publicacion_to_domain(self, orm: PublicacionORM) -> Publicacion:
        """Convierte PublicacionORM a Publicacion del dominio"""
        return Publicacion(
            id=orm.id,
            id_profesional=str(orm.profesional_id),
            titulo=orm.titulo,
            descripcion=orm.descripcion,
            especialidades=[self._especialidad_to_domain(orm.especialidad)],
        )

    def listar_especialidades(self) -> List[Especialidad]:
        """
        Lista todas las especialidades disponibles ordenadas alfabéticamente.

        Returns:
            Lista de especialidades del dominio
        """
        orms = (
            self.session.query(EspecialidadORM).order_by(EspecialidadORM.nombre).all()
        )
        return [self._especialidad_to_domain(orm) for orm in orms]

    def obtener_especialidad_por_id(self, id: int) -> Optional[Especialidad]:
        """
        Busca una especialidad por su ID.

        Args:
            id: ID de la especialidad

        Returns:
            Especialidad del dominio o None si no existe
        """
        orm = (
            self.session.query(EspecialidadORM)
            .filter(EspecialidadORM.id_especialidad == id)
            .first()
        )
        return self._especialidad_to_domain(orm) if orm else None

    def obtener_especialidad_por_nombre(self, nombre: str) -> Optional[Especialidad]:
        """
        Busca una especialidad por su nombre (case-insensitive).

        Args:
            nombre: Nombre de la especialidad

        Returns:
            Especialidad del dominio o None si no existe
        """
        orm = (
            self.session.query(EspecialidadORM)
            .filter(EspecialidadORM.nombre.ilike(nombre))
            .first()
        )
        return self._especialidad_to_domain(orm) if orm else None

    def crear_especialidad(
        self, nombre: str, descripcion: str, tarifa: Decimal
    ) -> Especialidad:
        """
        Crea una nueva especialidad.

        Args:
            nombre: Nombre de la especialidad
            descripcion: Descripción detallada
            tarifa: Tarifa base para la especialidad

        Returns:
            Especialidad creada

        Raises:
            ValueError: Si ya existe una especialidad con ese nombre
        """
        existente = self.obtener_especialidad_por_nombre(nombre)
        if existente:
            raise ValueError(f"Ya existe una especialidad con el nombre '{nombre}'")

        orm = EspecialidadORM(
            nombre=nombre.strip().title(),
            descripcion=descripcion.strip(),
            tarifa=tarifa,
        )
        self.session.add(orm)
        self.session.flush()

        return self._especialidad_to_domain(orm)

    def listar_publicaciones_por_profesional(
        self, profesional_id: UUID
    ) -> List[Publicacion]:
        """
        Lista todas las publicaciones de un profesional.

        Args:
            profesional_id: UUID del profesional

        Returns:
            Lista de publicaciones del dominio
        """
        orms = (
            self.session.query(PublicacionORM)
            .filter(PublicacionORM.profesional_id == profesional_id)
            .order_by(PublicacionORM.fecha_publicacion.desc())
            .all()
        )
        return [self._publicacion_to_domain(orm) for orm in orms]

    def obtener_publicacion_por_id(self, id: UUID) -> Optional[Publicacion]:
        """
        Busca una publicación por su ID.

        Args:
            id: UUID de la publicación

        Returns:
            Publicacion del dominio o None si no existe
        """
        orm = self.session.query(PublicacionORM).filter(PublicacionORM.id == id).first()
        return self._publicacion_to_domain(orm) if orm else None

    def crear_publicacion(
        self,
        profesional_id: UUID,
        especialidad_id: int,
        titulo: str,
        descripcion: str,
        fecha_publicacion: Optional[date] = None,
    ) -> Publicacion:
        """
        Crea una nueva publicación para un profesional.

        Args:
            profesional_id: UUID del profesional
            especialidad_id: ID de la especialidad
            titulo: Título de la publicación
            descripcion: Descripción/contenido de la publicación
            fecha_publicacion: Fecha de publicación (por defecto hoy)

        Returns:
            Publicacion creada

        Raises:
            ValueError: Si la especialidad no existe
        """
        especialidad = self.obtener_especialidad_por_id(especialidad_id)
        if not especialidad:
            raise ValueError(f"No existe la especialidad con ID {especialidad_id}")

        if fecha_publicacion is None:
            fecha_publicacion = date.today()

        orm = PublicacionORM(
            profesional_id=profesional_id,
            especialidad_id=especialidad_id,
            titulo=titulo.strip(),
            descripcion=descripcion.strip(),
            fecha_publicacion=fecha_publicacion,
        )
        self.session.add(orm)
        self.session.flush()

        return self._publicacion_to_domain(orm)

    def eliminar_publicacion(self, id: UUID) -> bool:
        """
        Elimina una publicación por su ID.

        Args:
            id: UUID de la publicación

        Returns:
            True si se eliminó, False si no existía
        """
        orm = self.session.query(PublicacionORM).filter(PublicacionORM.id == id).first()
        if orm:
            self.session.delete(orm)
            return True
        return False

    def obtener_tarifa_especialidad(self, especialidad_id: int) -> Optional[Decimal]:
        """
        Obtiene la tarifa actual de una especialidad.

        NOTA: Por ahora obtiene la tarifa base de la especialidad.
        En el futuro, si se implementa tabla de tarifas históricas,
        se buscará la tarifa vigente según fecha.

        Args:
            especialidad_id: ID de la especialidad

        Returns:
            Tarifa o None si no existe la especialidad
        """
        orm = (
            self.session.query(EspecialidadORM)
            .filter(EspecialidadORM.id_especialidad == especialidad_id)
            .first()
        )
        return orm.tarifa if orm else None
