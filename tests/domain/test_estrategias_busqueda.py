"""
Tests unitarios para las estrategias de búsqueda
"""

import pytest
from unittest.mock import Mock

from app.domain.strategies.estrategia import (
    EstrategiaBusqueda,
    BusquedaPorZona,
    BusquedaPorEspecialidad,
    BusquedaCombinada,
)

from app.domain.entities.catalogo import FiltroBusqueda


class TestBusquedaPorZona:
    """Tests para la estrategia de búsqueda por zona"""

    def test_busca_por_provincia(self, mock_profesional_repository_con_datos):
        """Búsqueda por provincia correctamente delegada"""
        estrategia = BusquedaPorZona()

        filtro = FiltroBusqueda(provincia="Buenos Aires")

        resultado = estrategia.buscar(mock_profesional_repository_con_datos, filtro)

        assert len(resultado) > 0
        mock_profesional_repository_con_datos.buscar_por_ubicacion.assert_called_once()

    def test_busca_por_provincia_departamento_barrio(
        self, mock_profesional_repository_con_datos
    ):
        """Búsqueda con todos los parámetros de ubicación"""
        estrategia = BusquedaPorZona()

        filtro = FiltroBusqueda(
            provincia="Buenos Aires", departamento="CABA", barrio="Flores"
        )

        resultado = estrategia.buscar(mock_profesional_repository_con_datos, filtro)

        assert isinstance(resultado, list)
        mock_profesional_repository_con_datos.buscar_por_ubicacion.assert_called_once_with(
            provincia="Buenos Aires", departamento="CABA", barrio="Flores"
        )


class TestBusquedaPorEspecialidad:
    """Tests para la estrategia de búsqueda por especialidad"""

    def test_busca_por_nombre_especialidad(self, mock_profesional_repository_con_datos):
        """Búsqueda por nombre de especialidad"""
        estrategia = BusquedaPorEspecialidad()

        filtro = FiltroBusqueda(nombre_especialidad="Cardiología")

        resultado = estrategia.buscar(mock_profesional_repository_con_datos, filtro)

        assert isinstance(resultado, list)
        mock_profesional_repository_con_datos.buscar_por_especialidad.assert_called_once_with(
            especialidad_id=None, especialidad_nombre="Cardiología"
        )

    def test_busca_por_id_especialidad(self, mock_profesional_repository_con_datos):
        """Búsqueda por ID de especialidad"""
        estrategia = BusquedaPorEspecialidad()

        filtro = FiltroBusqueda(id_especialidad=1)

        resultado = estrategia.buscar(mock_profesional_repository_con_datos, filtro)

        assert isinstance(resultado, list)


class TestBusquedaCombinada:
    """Tests para la estrategia de búsqueda combinada"""

    def test_busca_combinada_especialidad_provincia(
        self, mock_profesional_repository_con_datos
    ):
        """Búsqueda combinada: especialidad + provincia"""
        estrategia = BusquedaCombinada()

        filtro = FiltroBusqueda(
            nombre_especialidad="Cardiología", provincia="Buenos Aires"
        )

        resultado = estrategia.buscar(mock_profesional_repository_con_datos, filtro)

        assert isinstance(resultado, list)
        mock_profesional_repository_con_datos.buscar_combinado.assert_called_once()

    def test_busca_combinada_completa(self, mock_profesional_repository_con_datos):
        """Búsqueda combinada con todos los parámetros"""
        estrategia = BusquedaCombinada()

        filtro = FiltroBusqueda(
            nombre_especialidad="Cardiología",
            provincia="Buenos Aires",
            departamento="CABA",
            barrio="Flores",
        )

        resultado = estrategia.buscar(mock_profesional_repository_con_datos, filtro)

        assert isinstance(resultado, list)


class TestEstrategiaBusquedaAbstracta:
    """Tests para la clase abstracta EstrategiaBusqueda"""

    def test_no_puede_instanciarse_estrategia_abstracta(self):
        """No se puede instanciar directamente"""
        with pytest.raises(TypeError):
            EstrategiaBusqueda()

    def test_debe_implementar_metodo_buscar(self):
        """Todas las subclases deben implementar buscar()"""

        class EstrategiaIncompleta(EstrategiaBusqueda):
            pass

        with pytest.raises(TypeError):
            EstrategiaIncompleta()


class TestBusquedaEdgeCases:
    """Tests para casos edge"""

    def test_busqueda_retorna_lista_vacia(self, mock_profesional_repository):
        """Cuando no hay resultados, retorna lista vacía"""
        estrategia = BusquedaPorEspecialidad()

        mock_profesional_repository.buscar_por_especialidad.return_value = []

        from app.domain.entities.catalogo import FiltroBusqueda

        filtro = FiltroBusqueda(nombre_especialidad="EspecialidadQueNoExiste")

        resultado = estrategia.buscar(mock_profesional_repository, filtro)

        assert resultado == []

    def test_filtro_none_en_campos_opcionales(self):
        """Los campos None en el filtro deben ser ignorados"""
        estrategia = BusquedaPorEspecialidad()
        repo = Mock()

        filtro = FiltroBusqueda(
            nombre_especialidad="Cardiología", provincia=None, barrio=None
        )

        repo.buscar_por_especialidad.return_value = []
        resultado = estrategia.buscar(repo, filtro)
        assert resultado == []
