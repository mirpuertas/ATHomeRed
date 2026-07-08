from __future__ import annotations
from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from typing import List, Optional
from ..enumeraciones import DiaSemana


@dataclass(frozen=True)
class Ubicacion:
    """Valor: describe una ubicación física (normalizada por catálogo en la DB)."""

    provincia: str
    departamento: str
    barrio: str
    calle: str
    numero: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    def __post_init__(self):
        if self.latitud is not None and not (-90.0 <= self.latitud <= 90.0):
            raise ValueError("latitud fuera de rango [-90, 90]")
        if self.longitud is not None and not (-180.0 <= self.longitud <= 180.0):
            raise ValueError("longitud fuera de rango [-180, 180]")


@dataclass(frozen=True)
class Disponibilidad:
    dias_semana: List[DiaSemana]
    hora_inicio: time
    hora_fin: time

    def __post_init__(self):
        if self.hora_inicio >= self.hora_fin:
            raise ValueError("hora_inicio debe ser < hora_fin")


@dataclass(frozen=True)
class Vigencia:
    vigente_desde: date
    vigente_hasta: Optional[date] = None

    def vigente_en(self, fecha: date) -> bool:
        if fecha < self.vigente_desde:
            return False
        if self.vigente_hasta is None:
            return True
        return self.vigente_desde <= fecha <= self.vigente_hasta


@dataclass(frozen=True)
class Matricula:
    """Valor: matrícula profesional con vigencia provincial."""

    numero: str
    provincia: str
    vigente_desde: date
    vigente_hasta: Optional[date] = None

    def __post_init__(self):
        if self.vigente_hasta is not None and self.vigente_hasta < self.vigente_desde:
            raise ValueError("vigente_hasta < vigente_desde")

    def esta_vigente_en(self, fecha: date) -> bool:
        if fecha < self.vigente_desde:
            return False
        if self.vigente_hasta is None:
            return True
        return self.vigente_desde <= fecha <= self.vigente_hasta


@dataclass(frozen=True)
class Dinero:
    """Valor: dinero con validación mínima (monto >= 0). Moneda se maneja como ISO 4217."""

    monto: Decimal
    moneda: str = "ARS"

    def __post_init__(self):
        if self.monto < Decimal("0"):
            raise ValueError("El monto no puede ser negativo")
        if len(self.moneda) != 3:
            raise ValueError("Código de moneda debe ser ISO-4217 de 3 letras")
