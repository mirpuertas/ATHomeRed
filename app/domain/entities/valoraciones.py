from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID


@dataclass
class Valoracion:
    id: UUID
    id_profesional: UUID
    id_paciente: UUID
    puntuacion: int
    comentario: Optional[str] = None
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not (1 <= self.puntuacion <= 5):
            raise ValueError("La puntuación debe estar entre 1 y 5")


def promedio_valoraciones(
    valoraciones: list[Valoracion], id_profesional: UUID
) -> float:
    """Devuelve el promedio de valoraciones (o 0.0 si no hay ninguna)."""
    propias = [v.puntuacion for v in valoraciones if v.id_profesional == id_profesional]
    return sum(propias) / len(propias) if propias else 0.0
