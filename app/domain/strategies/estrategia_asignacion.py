from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.agenda import Consulta
    from app.domain.entities.usuarios import Profesional


class AsignacionStrategy(ABC):
    @abstractmethod
    def validar(self, cita: "Consulta", profesional: "Profesional") -> bool:
        pass


class DisponibilidadHorariaStrategy(AsignacionStrategy):
    def validar(self, cita: "Consulta", profesional) -> bool:
        for disponibilidad in profesional.disponibilidades:
            if (
                disponibilidad.fecha == cita.fecha
                and disponibilidad.hora_inicio == cita.hora_inicio
            ):
                return False
        return True


class MatriculaProvinciaStrategy(AsignacionStrategy):
    def validar(self, cita: "Consulta", profesional) -> bool:
        return any(
            m.provincia == cita.ubicacion.provincia for m in profesional.matriculas
        )
