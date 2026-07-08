from __future__ import annotations
import datetime as dt
from abc import ABC
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from ..value_objects.objetos_valor import Ubicacion, Disponibilidad, Matricula
from .catalogo import Especialidad


@dataclass
class Usuario(ABC):
    """
    Usuario del sistema: persona con cuenta de acceso.
    Puede ser Profesional o Solicitante.
    """

    id: UUID
    nombre: str
    apellido: str
    email: str
    celular: str
    ubicacion: Ubicacion
    activo: bool = True

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    def activar(self) -> None:
        self.activo = True

    def desactivar(self) -> None:
        self.activo = False

    def datos_contacto(self) -> str:
        return f"{self.nombre_completo} <{self.email}> ({self.celular or 's/teléfono'})"


@dataclass
class Profesional(Usuario):
    """
    Usuario que ofrece servicios profesionales de salud.
    Hereda de Usuario (tiene cuenta y credenciales).

    REGLA DE NEGOCIO: Todo profesional debe tener al menos una matrícula activa.
    Las matrículas se almacenan en la tabla 'matricula' (relación 1:N).
    """

    verificado: bool = False
    especialidades: List[Especialidad] = field(default_factory=list)
    disponibilidades: List[Disponibilidad] = field(default_factory=list)
    matriculas: List[Matricula] = field(default_factory=list)

    def agregar_disponibilidad(self, d: Disponibilidad) -> None:
        self.disponibilidades.append(d)

    def tiene_matricula_valida(self) -> bool:
        """Verifica que el profesional tenga al menos una matrícula activa"""
        return len(self.matriculas) > 0

    def agregar_matricula(self, m: Matricula) -> None:
        """Agrega una matrícula al profesional"""
        if m not in self.matriculas:
            self.matriculas.append(m)


@dataclass
class Solicitante(Usuario):
    """
    Usuario que solicita turnos médicos.
    Puede ser para sí mismo (auto-gestión) o para personas a su cargo (dependientes).
    Hereda de Usuario (tiene cuenta y credenciales).
    """

    pacientes: List["Paciente"] = field(default_factory=list)

    def agregar_paciente(self, paciente: "Paciente") -> None:
        """Agrega un paciente a cargo de este solicitante"""
        if paciente not in self.pacientes:
            self.pacientes.append(paciente)


@dataclass
class Paciente:
    """
    Persona que recibe servicios médicos.
    NO hereda de Usuario: puede o no tener cuenta propia.

    - Si es auto-gestionado: el Solicitante es el mismo paciente
    - Si es dependiente: el Solicitante es tutor/familiar

    El email/celular de contacto se obtienen del Solicitante asociado.
    """

    id: UUID
    nombre: str
    apellido: str
    fecha_nacimiento: dt.date
    ubicacion: Ubicacion
    solicitante_id: UUID
    relacion: str = "self"
    notas: str = ""

    def edad(self, hoy: Optional[dt.date] = None) -> int:
        """Calcula la edad del paciente"""
        hoy = hoy or dt.date.today()
        years = hoy.year - self.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (
            self.fecha_nacimiento.month,
            self.fecha_nacimiento.day,
        ):
            years -= 1
        return years

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    def es_menor_de_edad(self, hoy: Optional[dt.date] = None) -> bool:
        """Verifica si el paciente es menor de 18 años"""
        return self.edad(hoy) < 18

    def es_auto_gestionado(self) -> bool:
        """Verifica si el paciente gestiona sus propios turnos"""
        return self.relacion.lower() == "self"
