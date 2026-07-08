from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal
from datetime import date


@dataclass
class Especialidad:
    id: int
    nombre: str
    tarifa: Decimal


@dataclass
class Tarifa:
    """
    DEPRECATED: Tarifa ahora está directamente en Especialidad.
    Esta clase queda para referencia futura si se implementa historial de tarifas.
    """

    id: int
    id_especialidad: int
    monto: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date] = None

    def vigente_en(self, fecha: date) -> bool:
        if fecha < self.vigente_desde:
            return False
        if self.vigente_hasta is None:
            return True
        return self.vigente_desde <= fecha <= self.vigente_hasta


@dataclass
class Publicacion:
    """Aviso de un profesional (texto + especialidades asociadas)."""

    id: int
    id_profesional: str
    titulo: str
    descripcion: str
    especialidades: List[Especialidad]


@dataclass(frozen=True)
class FiltroBusqueda:
    id_especialidad: Optional[int] = None
    nombre_especialidad: Optional[str] = None
    barrio: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    texto: Optional[str] = None
    ordenar_por_distancia: bool = False
