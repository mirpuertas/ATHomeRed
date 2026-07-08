from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from uuid import UUID
from datetime import datetime


@dataclass
class Event:
    """Evento base del dominio"""

    tipo: str
    cita_id: UUID
    datos: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CitaCreada(Event):
    """Se creó una nueva cita"""

    def __init__(
        self, cita_id: UUID, profesional_id: UUID, paciente_id: UUID, **kwargs
    ):
        super().__init__(
            tipo="cita.creada",
            cita_id=cita_id,
            datos={
                "profesional_id": str(profesional_id),
                "paciente_id": str(paciente_id),
                **kwargs,
            },
        )


@dataclass
class CitaConfirmada(Event):
    """Se confirmó una cita"""

    def __init__(self, cita_id: UUID, confirmado_por: str = None):
        super().__init__(
            tipo="cita.confirmada",
            cita_id=cita_id,
            datos={"confirmado_por": confirmado_por},
        )


@dataclass
class CitaCancelada(Event):
    """Se canceló una cita"""

    def __init__(self, cita_id: UUID, motivo: str = None, cancelado_por: str = None):
        super().__init__(
            tipo="cita.cancelada",
            cita_id=cita_id,
            datos={"motivo": motivo, "cancelado_por": cancelado_por},
        )


@dataclass
class CitaReprogramada(Event):
    """Se reprogramó una cita"""

    def __init__(self, cita_id: UUID, fecha_anterior: str, fecha_nueva: str, **kwargs):
        super().__init__(
            tipo="cita.reprogramada",
            cita_id=cita_id,
            datos={
                "fecha_anterior": fecha_anterior,
                "fecha_nueva": fecha_nueva,
                **kwargs,
            },
        )


@dataclass
class CitaCompletada(Event):
    """Se completó una cita"""

    def __init__(self, cita_id: UUID, notas: str = None):
        super().__init__(
            tipo="cita.completada", cita_id=cita_id, datos={"notas": notas}
        )
