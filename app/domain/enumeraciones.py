from __future__ import annotations
from enum import IntEnum, Enum


class DiaSemana(IntEnum):
    """Días de la semana (1=Lunes, 7=Domingo)"""

    LUNES = 1
    MARTES = 2
    MIERCOLES = 3
    JUEVES = 4
    VIERNES = 5
    SABADO = 6
    DOMINGO = 7


class EstadoCita(str, Enum):
    """Estados posibles de una cita/consulta"""

    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    REPROGRAMADA = "reprogramada"
