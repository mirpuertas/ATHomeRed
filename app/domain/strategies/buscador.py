from __future__ import annotations
from dataclasses import dataclass, field

from app.domain.entities.catalogo import FiltroBusqueda
from app.domain.entities.usuarios import Profesional
from app.infra.repositories.profesional_repository import ProfesionalRepository
from .estrategia import EstrategiaBusqueda


@dataclass
class Buscador:
    repo: ProfesionalRepository
    estrategia: EstrategiaBusqueda
    profesionales: list[Profesional] = field(default_factory=list)

    def cambiar_estrategia(self, estrategia: EstrategiaBusqueda) -> None:
        self.estrategia = estrategia

    def buscar(self, filtro: FiltroBusqueda) -> list[Profesional]:
        self.profesionales = self.estrategia.buscar(self.repo, filtro)
        return self.profesionales
