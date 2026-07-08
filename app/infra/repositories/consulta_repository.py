from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.entities.agenda import Cita
from app.domain.enumeraciones import EstadoCita
from app.domain.value_objects.objetos_valor import Ubicacion
from app.domain.eventos import Event
from app.infra.persistence.agenda import (
    ConsultaORM,
    EventoORM,
    EstadoConsultaORM,
)
from app.infra.persistence.perfiles import ProfesionalORM


class ConsultaRepository:
    """
    Repositorio para gestionar la persistencia de Citas/Consultas.
    Implementa el patrón Repository para abstraer el acceso a datos.
    """

    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, orm: ConsultaORM) -> Cita:
        """
        Convierte un modelo ORM a entidad de dominio.

        Args:
            orm: Modelo ORM de la consulta

        Returns:
            Entidad Cita del dominio
        """
        estado_codigo = orm.estado.codigo if orm.estado else "pendiente"

        ubicacion = None
        if orm.direccion_servicio:
            dir_orm = orm.direccion_servicio
            ubicacion = Ubicacion(
                provincia=dir_orm.barrio.departamento.provincia.nombre,
                departamento=dir_orm.barrio.departamento.nombre,
                barrio=dir_orm.barrio.nombre,
                calle=dir_orm.calle,
                numero=str(dir_orm.numero),
                latitud=dir_orm.latitud,
                longitud=dir_orm.longitud,
            )

        return Cita(
            id=orm.id,
            paciente_id=orm.paciente_id,
            profesional_id=orm.profesional_id,
            fecha=orm.fecha,
            hora_inicio=orm.hora_inicio,
            hora_fin=orm.hora_fin,
            ubicacion=ubicacion,
            estado=EstadoCita(estado_codigo),
            notas=orm.notas or "",
        )

    def _to_orm(self, cita: Cita, orm: ConsultaORM = None) -> ConsultaORM:
        """
        Convierte una entidad de dominio a modelo ORM.

        Args:
            cita: Entidad Cita del dominio
            orm: Modelo ORM existente (para actualización)

        Returns:
            Modelo ORM de la consulta
        """
        estado_orm = (
            self.session.query(EstadoConsultaORM)
            .filter(EstadoConsultaORM.codigo == cita.estado.value)
            .first()
        )

        if not estado_orm:
            estado_orm = EstadoConsultaORM(
                codigo=cita.estado.value, descripcion=cita.estado.value.upper()
            )
            self.session.add(estado_orm)
            self.session.flush()

        if orm is None:
            orm = ConsultaORM(
                id=cita.id,
                paciente_id=cita.paciente_id,
                profesional_id=cita.profesional_id,
                fecha=cita.fecha,
                hora_inicio=cita.hora_inicio,
                hora_fin=cita.hora_fin,
                estado_id=estado_orm.id,
                notas=cita.notas,
            )
        else:
            orm.fecha = cita.fecha
            orm.hora_inicio = cita.hora_inicio
            orm.hora_fin = cita.hora_fin
            orm.estado_id = estado_orm.id
            orm.notas = cita.notas

        return orm

    def obtener_por_id(self, id: UUID) -> Optional[Cita]:
        """
        Obtiene una cita por su ID.

        Args:
            id: UUID de la cita

        Returns:
            Cita o None si no existe
        """
        orm = self.session.query(ConsultaORM).filter(ConsultaORM.id == id).first()

        return self._to_domain(orm) if orm else None

    def listar_por_profesional(
        self,
        profesional_id: UUID,
        desde: date = None,
        hasta: date = None,
        solo_activas: bool = False,
    ) -> List[Cita]:
        """
        Lista las citas de un profesional.

        Args:
            profesional_id: UUID del profesional
            desde: Fecha inicial (opcional)
            hasta: Fecha final (opcional)
            solo_activas: Si True, excluye canceladas y completadas

        Returns:
            Lista de citas
        """
        query = self.session.query(ConsultaORM).filter(
            ConsultaORM.profesional_id == profesional_id
        )

        if desde:
            query = query.filter(ConsultaORM.fecha >= desde)

        if hasta:
            query = query.filter(ConsultaORM.fecha <= hasta)

        if solo_activas:
            query = query.join(EstadoConsultaORM).filter(
                EstadoConsultaORM.codigo.notin_(["cancelada", "completada"])
            )

        query = query.order_by(ConsultaORM.fecha, ConsultaORM.hora_inicio)

        return [self._to_domain(orm) for orm in query.all()]

    def listar_por_paciente(
        self, paciente_id: UUID, desde: date = None, solo_activas: bool = False
    ) -> List[Cita]:
        """
        Lista las citas de un paciente.

        Args:
            paciente_id: UUID del paciente
            desde: Fecha inicial (opcional)
            solo_activas: Si True, excluye canceladas y completadas

        Returns:
            Lista de citas
        """
        query = self.session.query(ConsultaORM).filter(
            ConsultaORM.paciente_id == paciente_id
        )

        if desde:
            query = query.filter(ConsultaORM.fecha >= desde)

        if solo_activas:
            query = query.join(EstadoConsultaORM).filter(
                EstadoConsultaORM.codigo.notin_(["cancelada", "completada"])
            )

        query = query.order_by(ConsultaORM.fecha.desc(), ConsultaORM.hora_inicio)

        return [self._to_domain(orm) for orm in query.all()]

    def crear(self, cita: Cita, direccion_id: Optional[UUID] = None) -> Cita:
        """
        Crea una nueva cita en la base de datos.

        Args:
            cita: Entidad Cita del dominio
            direccion_id: UUID de la dirección del servicio

        Returns:
            Cita creada con datos actualizados
        """
        orm = self._to_orm(cita)

        if direccion_id is None:
            prof_orm = (
                self.session.query(ProfesionalORM)
                .filter(ProfesionalORM.id == cita.profesional_id)
                .first()
            )
            if not prof_orm or not prof_orm.direccion_id:
                raise ValueError(
                    "El profesional no tiene una dirección de servicio configurada"
                )
            direccion_id = prof_orm.direccion_id

        orm.direccion_servicio_id = direccion_id

        self.session.add(orm)
        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def actualizar(self, cita: Cita) -> Cita:
        """
        Actualiza una cita existente.

        Args:
            cita: Entidad Cita con datos actualizados

        Returns:
            Cita actualizada o None si no existe
        """
        orm = self.session.query(ConsultaORM).filter(ConsultaORM.id == cita.id).first()

        if not orm:
            return None

        orm = self._to_orm(cita, orm)
        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def eliminar(self, id: UUID) -> bool:
        """
        Elimina una cita (hard delete).

        Args:
            id: UUID de la cita

        Returns:
            True si se eliminó, False si no existía
        """
        orm = self.session.query(ConsultaORM).filter(ConsultaORM.id == id).first()

        if not orm:
            return False

        self.session.delete(orm)
        self.session.commit()
        return True

    def verificar_disponibilidad(
        self, profesional_id: UUID, fecha: date, hora_inicio, hora_fin
    ) -> bool:
        """
        Verifica si el profesional está disponible en el horario indicado.

        Args:
            profesional_id: UUID del profesional
            fecha: Fecha de la cita
            hora_inicio: Hora de inicio
            hora_fin: Hora de fin

        Returns:
            True si está disponible, False si hay conflicto
        """
        citas_existentes = (
            self.session.query(ConsultaORM)
            .join(EstadoConsultaORM)
            .filter(
                ConsultaORM.profesional_id == profesional_id,
                ConsultaORM.fecha == fecha,
                EstadoConsultaORM.codigo != "cancelada",
            )
            .all()
        )

        for cita_orm in citas_existentes:
            if hora_inicio < cita_orm.hora_fin and hora_fin > cita_orm.hora_inicio:
                return False

        return True

    def guardar_evento(self, evento: Event) -> None:
        """
        Persiste un evento del dominio.

        Args:
            evento: Evento a persistir
        """
        evento_orm = EventoORM(
            consulta_id=evento.cita_id, tipo=evento.tipo, datos=evento.datos
        )
        self.session.add(evento_orm)
        self.session.commit()

    def obtener_eventos(self, cita_id: UUID) -> List[Event]:
        """
        Obtiene todos los eventos de una cita.

        Args:
            cita_id: UUID de la cita

        Returns:
            Lista de eventos
        """
        eventos_orm = (
            self.session.query(EventoORM)
            .filter(EventoORM.consulta_id == cita_id)
            .order_by(EventoORM.id)
            .all()
        )

        return [
            Event(tipo=e.tipo, cita_id=e.consulta_id, datos=e.datos)
            for e in eventos_orm
        ]
