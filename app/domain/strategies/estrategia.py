from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.usuarios import Profesional
from app.domain.entities.catalogo import FiltroBusqueda
from app.infra.repositories.profesional_repository import ProfesionalRepository

"""
Estrategias de búsqueda de profesionales (Patrón Strategy - GoF)

Responsabilidades:
- Definir diferentes algoritmos de búsqueda (por zona, especialidad, combinado)
- Validar que los filtros sean coherentes antes de delegar al repositorio
- Delegar la ejecución de queries al ProfesionalRepository

Ventajas de esta arquitectura:
- Separación de responsabilidades: Las estrategias validan lógica de negocio,
  el repositorio maneja persistencia
- Fácil de extender: Agregar nuevas estrategias sin modificar código existente
- Testeable: Se puede mockear el repositorio para tests unitarios
"""


class EstrategiaBusqueda(ABC):
    @abstractmethod
    def buscar(
        self, repo: ProfesionalRepository, filtro: FiltroBusqueda
    ) -> List[Profesional]:
        pass


class BusquedaPorZona(EstrategiaBusqueda):
    def buscar(
        self, repo: ProfesionalRepository, filtro: FiltroBusqueda
    ) -> list[Profesional]:
        return repo.buscar_por_ubicacion(
            provincia=filtro.provincia,
            departamento=filtro.departamento,
            barrio=filtro.barrio,
        )


class BusquedaPorEspecialidad(EstrategiaBusqueda):
    def buscar(
        self, repo: ProfesionalRepository, filtro: FiltroBusqueda
    ) -> list[Profesional]:
        return repo.buscar_por_especialidad(
            especialidad_id=filtro.id_especialidad,
            especialidad_nombre=filtro.nombre_especialidad,
        )


class BusquedaCombinada(EstrategiaBusqueda):
    def buscar(
        self, repo: ProfesionalRepository, filtro: FiltroBusqueda
    ) -> list[Profesional]:
        return repo.buscar_combinado(
            especialidad_id=filtro.id_especialidad,
            especialidad_nombre=filtro.nombre_especialidad,
            provincia=filtro.provincia,
            departamento=filtro.departamento,
            barrio=filtro.barrio,
        )
