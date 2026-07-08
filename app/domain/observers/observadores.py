from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Callable, Dict
from logging import getLogger

logger = getLogger(__name__)


class Observer(ABC):
    """Interfaz base para observadores de eventos del dominio"""

    @abstractmethod
    def update(self, evt) -> None:
        """Procesa un evento"""
        pass


class Subject(ABC):
    """Sujeto que notifica a observadores (patrón GoF)"""

    def __init__(self):
        self.observers: List[Observer] = []

    def attach(self, obs: Observer) -> None:
        """Suscribir observador"""
        if obs not in self.observers:
            self.observers.append(obs)

    def detach(self, obs: Observer) -> None:
        """Desuscribir observador"""
        if obs in self.observers:
            self.observers.remove(obs)

    def notify(self, evt) -> None:
        """Notificar a todos los observadores"""
        for obs in self.observers:
            obs.update(evt)


class NotificadorEmail(Observer):
    """
    Observador que simula envío de notificaciones por email.
    Escucha eventos de citas y genera notificaciones.
    """

    def update(self, evt) -> None:
        """Procesa evento y envía notificación simulada"""
        tipo_evento = getattr(evt, "tipo", "desconocido")

        if tipo_evento == "cita.creada":
            self._notificar_cita_creada(evt)
        elif tipo_evento == "cita.confirmada":
            self._notificar_cita_confirmada(evt)
        elif tipo_evento == "cita.cancelada":
            self._notificar_cita_cancelada(evt)
        elif tipo_evento == "cita.reprogramada":
            self._notificar_cita_reprogramada(evt)
        elif tipo_evento == "cita.completada":
            self._notificar_cita_completada(evt)

    def _notificar_cita_creada(self, evt) -> None:
        """Notifica creación de cita a profesional y solicitante"""
        cita_id = evt.cita_id
        prof_id = evt.datos.get("profesional_id")
        pac_id = evt.datos.get("paciente_id")

        print(
            f"\n ========== NOTIFICADOR EMAIL ==========\n"
            f"    Evento: CITA CREADA\n"
            f"    Cita ID: {cita_id}\n"
            f"    Profesional: {prof_id}\n"
            f"    Paciente: {pac_id}\n"
            f"    Email enviado a profesional y solicitante\n"
            f"    {evt.timestamp}\n"
            f"   ========================================\n"
        )
        logger.info(f" Notificación: CitaCreada {cita_id}")

    def _notificar_cita_confirmada(self, evt) -> None:
        """Notifica confirmación de cita"""
        cita_id = evt.cita_id
        confirmado_por = evt.datos.get("confirmado_por", "Sistema")

        print(
            f"\n ========== NOTIFICADOR EMAIL ==========\n"
            f"    Evento: CITA CONFIRMADA\n"
            f"    Cita ID: {cita_id}\n"
            f"    Confirmado por: {confirmado_por}\n"
            f"    Email enviado a profesional y solicitante\n"
            f"    {evt.timestamp}\n"
            f"   ========================================\n"
        )
        logger.info(f" Notificación: CitaConfirmada {cita_id}")

    def _notificar_cita_cancelada(self, evt) -> None:
        """Notifica cancelación de cita"""
        cita_id = evt.cita_id
        motivo = evt.datos.get("motivo", "No especificado")
        cancelado_por = evt.datos.get("cancelado_por", "Sistema")

        print(
            f"\n ========== NOTIFICADOR EMAIL ==========\n"
            f"    Evento: CITA CANCELADA\n"
            f"    Cita ID: {cita_id}\n"
            f"    Motivo: {motivo}\n"
            f"    Cancelado por: {cancelado_por}\n"
            f"    Email enviado a profesional y solicitante\n"
            f"    {evt.timestamp}\n"
            f"   ========================================\n"
        )
        logger.warning(f" Notificación: CitaCancelada {cita_id}")

    def _notificar_cita_reprogramada(self, evt) -> None:
        """Notifica reprogramación de cita"""
        cita_id = evt.cita_id
        fecha_anterior = evt.datos.get("fecha_anterior")
        fecha_nueva = evt.datos.get("fecha_nueva")

        print(
            f"\n ========== NOTIFICADOR EMAIL ==========\n"
            f"    Evento: CITA REPROGRAMADA\n"
            f"    Cita ID: {cita_id}\n"
            f"    Fecha anterior: {fecha_anterior}\n"
            f"    Fecha nueva: {fecha_nueva}\n"
            f"    Email enviado a profesional y solicitante\n"
            f"    {evt.timestamp}\n"
            f"   ========================================\n"
        )
        logger.info(f" Notificación: CitaReprogramada {cita_id}")

    def _notificar_cita_completada(self, evt) -> None:
        """Notifica completación de cita"""
        cita_id = evt.cita_id
        notas = evt.datos.get("notas", "Sin notas")

        print(
            f"\n ========== NOTIFICADOR EMAIL ==========\n"
            f"    Evento: CITA COMPLETADA\n"
            f"    Cita ID: {cita_id}\n"
            f"    Notas: {notas}\n"
            f"    Email enviado a profesional y solicitante\n"
            f"    {evt.timestamp}\n"
            f"   ========================================\n"
        )
        logger.info(f" Notificación: CitaCompletada {cita_id}")


class AuditLogger(Observer):
    """
    Observador para auditoría (v3 - pendiente).
    Por ahora solo registra en logs.
    """

    def update(self, evt) -> None:
        """Registra evento en auditoría"""
        tipo_evento = getattr(evt, "tipo", "desconocido")
        cita_id = getattr(evt, "cita_id", "N/A")

        logger.info(f"[AUDIT] Evento: {tipo_evento} | Cita: {cita_id}")


class EventBus:
    """
    Bus de eventos simple para publicar/suscribir eventos.
    Desacopla el dominio de los observadores.
    """

    def __init__(self):
        self._suscriptores: Dict[str, List[Callable]] = {}

    def suscribir(self, tipo_evento: str, handler: Callable) -> None:
        """Suscribir handler a un tipo de evento"""
        if tipo_evento not in self._suscriptores:
            self._suscriptores[tipo_evento] = []
        self._suscriptores[tipo_evento].append(handler)

    def publicar(self, evt) -> None:
        """Publicar evento a todos los suscriptores"""
        tipo_evento = getattr(evt, "tipo", "desconocido")

        if tipo_evento in self._suscriptores:
            for handler in self._suscriptores[tipo_evento]:
                try:
                    handler(evt)
                except Exception as e:
                    logger.error(f"Error procesando evento {tipo_evento}: {str(e)}")

    def suscribir_observer(self, tipo_evento: str, observer: Observer) -> None:
        """Suscribir Observer tradicional a un tipo de evento"""

        def handler(evt):
            observer.update(evt)

        self.suscribir(tipo_evento, handler)
