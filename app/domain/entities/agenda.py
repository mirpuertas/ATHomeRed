from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, datetime, timedelta
from typing import List
from uuid import UUID

from ..value_objects.objetos_valor import Ubicacion
from ..enumeraciones import EstadoCita
from ..eventos import (
    CitaConfirmada,
    CitaCancelada,
    CitaReprogramada,
    CitaCompletada,
)
from ..observers.observadores import Subject


@dataclass
class Cita(Subject):
    """
    Entidad de agenda: una cita entre paciente y profesional.

    Implementa el patrón Observer para notificar cambios de estado.
    El monto se obtiene de la tarifa de la especialidad del profesional.
    """

    id: UUID
    paciente_id: UUID
    profesional_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    ubicacion: Ubicacion
    estado: EstadoCita = EstadoCita.PENDIENTE
    notas: str = ""
    motivo_consulta: str = ""
    creado_en: datetime = field(default_factory=datetime.now)
    actualizado_en: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validaciones al crear la cita"""
        super().__init__()

        if self.hora_inicio >= self.hora_fin:
            raise ValueError("hora_inicio debe ser anterior a hora_fin")

        duracion = datetime.combine(date.today(), self.hora_fin) - datetime.combine(
            date.today(), self.hora_inicio
        )
        if duracion < timedelta(minutes=30):
            raise ValueError("La cita debe durar al menos 30 minutos")

        if duracion > timedelta(hours=4):
            raise ValueError("La cita no puede durar más de 4 horas")

    @property
    def duracion(self) -> timedelta:
        """Duración de la cita"""
        return datetime.combine(date.today(), self.hora_fin) - datetime.combine(
            date.today(), self.hora_inicio
        )

    @property
    def esta_pendiente(self) -> bool:
        return self.estado == EstadoCita.PENDIENTE

    @property
    def esta_confirmada(self) -> bool:
        return self.estado == EstadoCita.CONFIRMADA

    @property
    def esta_cancelada(self) -> bool:
        return self.estado == EstadoCita.CANCELADA

    @property
    def esta_completada(self) -> bool:
        return self.estado == EstadoCita.COMPLETADA

    @property
    def puede_modificarse(self) -> bool:
        """Indica si la cita puede modificarse (no está completada ni cancelada)"""
        return self.estado not in [EstadoCita.COMPLETADA, EstadoCita.CANCELADA]

    def confirmar(self, confirmado_por: str = None) -> None:
        """
        Confirma una cita pendiente.

        Args:
            confirmado_por: Usuario que confirmó la cita

        Raises:
            ValueError: Si la cita no está en estado PENDIENTE
        """
        if self.estado != EstadoCita.PENDIENTE:
            raise ValueError(
                f"Solo se pueden confirmar citas pendientes. Estado actual: {self.estado.value}"
            )

        self.estado = EstadoCita.CONFIRMADA
        self.actualizado_en = datetime.now()

        self.notify(CitaConfirmada(cita_id=self.id, confirmado_por=confirmado_por))

    def cancelar(self, motivo: str = None, cancelado_por: str = None) -> None:
        """
        Cancela una cita.

        Args:
            motivo: Motivo de la cancelación
            cancelado_por: Usuario que canceló la cita

        Raises:
            ValueError: Si la cita ya está completada
        """
        if self.estado == EstadoCita.COMPLETADA:
            raise ValueError("No se puede cancelar una cita completada")

        self.estado = EstadoCita.CANCELADA
        self.actualizado_en = datetime.now()

        if motivo:
            self.notas = f"{self.notas}\nCancelada: {motivo}".strip()

        self.notify(
            CitaCancelada(cita_id=self.id, motivo=motivo, cancelado_por=cancelado_por)
        )

    def completar(self, notas_finales: str = None) -> None:
        """
        Marca la cita como completada.

        Args:
            notas_finales: Notas finales de la consulta

        Raises:
            ValueError: Si la cita no está confirmada o reprogramada
        """
        if self.estado not in [EstadoCita.CONFIRMADA, EstadoCita.REPROGRAMADA]:
            raise ValueError(
                f"Solo se pueden completar citas confirmadas o reprogramadas. Estado actual: {self.estado.value}"
            )

        self.estado = EstadoCita.COMPLETADA
        self.actualizado_en = datetime.now()

        if notas_finales:
            self.notas = f"{self.notas}\n{notas_finales}".strip()

        self.notify(CitaCompletada(cita_id=self.id, notas=notas_finales))

    def reprogramar(
        self, nueva_fecha: date, nueva_hora_inicio: time, nueva_hora_fin: time
    ) -> None:
        """
        Reprograma una cita.

        Args:
            nueva_fecha: Nueva fecha de la cita
            nueva_hora_inicio: Nueva hora de inicio
            nueva_hora_fin: Nueva hora de fin

        Raises:
            ValueError: Si la cita no puede modificarse o los horarios son inválidos
        """
        if not self.puede_modificarse:
            raise ValueError(
                f"No se puede reprogramar una cita en estado {self.estado.value}"
            )

        if nueva_hora_inicio >= nueva_hora_fin:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin")

        fecha_anterior = f"{self.fecha} {self.hora_inicio}-{self.hora_fin}"
        fecha_nueva = f"{nueva_fecha} {nueva_hora_inicio}-{nueva_hora_fin}"

        self.fecha = nueva_fecha
        self.hora_inicio = nueva_hora_inicio
        self.hora_fin = nueva_hora_fin
        self.estado = EstadoCita.REPROGRAMADA
        self.actualizado_en = datetime.now()

        self.notify(
            CitaReprogramada(
                cita_id=self.id,
                fecha_anterior=fecha_anterior,
                fecha_nueva=fecha_nueva,
            )
        )

    def agregar_nota(self, nota: str) -> None:
        """Agrega una nota a la consulta"""
        self.notas = f"{self.notas}\n{nota}".strip()
        self.actualizado_en = datetime.now()

    def validar_conflicto_horario(self, otras_citas: List["Cita"]) -> bool:
        """
        Verifica si esta cita tiene conflicto de horario con otras citas.

        Args:
            otras_citas: Lista de otras citas del mismo profesional

        Returns:
            True si hay conflicto, False en caso contrario
        """
        for otra in otras_citas:
            if otra.fecha != self.fecha or otra.esta_cancelada:
                continue

            if self.hora_inicio < otra.hora_fin and self.hora_fin > otra.hora_inicio:
                return True

        return False

    def __str__(self) -> str:
        return f"Cita({self.id}) - {self.fecha} {self.hora_inicio}-{self.hora_fin} [{self.estado.value}]"
