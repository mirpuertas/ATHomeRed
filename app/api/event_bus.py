"""
Event Bus: Sistema centralizado de publicación de eventos.

Desacopla el dominio de los observadores. Los eventos se publican
desde los routers y los observadores se suscriben sin que el dominio
lo sepa.
"""

from app.domain.observers.observadores import EventBus, NotificadorEmail

event_bus = EventBus()

notificador_email = NotificadorEmail()

_EVENTOS_NOTIFICABLES = [
    "cita.creada",
    "cita.confirmada",
    "cita.cancelada",
    "cita.reprogramada",
    "cita.completada",
]

for evento in _EVENTOS_NOTIFICABLES:
    event_bus.suscribir_observer(evento, notificador_email)


def get_event_bus() -> EventBus:
    """Dependency injection para obtener el event bus"""
    return event_bus
