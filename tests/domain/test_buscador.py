"""
Tests unitarios para el Buscador
"""

from app.domain.strategies.buscador import Buscador
from app.domain.strategies.estrategia import (
    BusquedaPorZona,
    BusquedaPorEspecialidad,
    BusquedaCombinada,
)
from app.domain.entities.catalogo import FiltroBusqueda


class TestBuscador:
    """Tests para la clase Buscador"""

    def test_inicializacion(self, mock_profesional_repository_con_datos):
        """El Buscador se inicializa correctamente"""
        estrategia = BusquedaPorEspecialidad()
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos, estrategia=estrategia
        )

        assert buscador.repo is mock_profesional_repository_con_datos
        assert buscador.estrategia is estrategia
        assert buscador.profesionales == []

    def test_cambiar_estrategia(self, mock_profesional_repository_con_datos):
        """El Buscador puede cambiar de estrategia"""
        estrategia1 = BusquedaPorZona()
        estrategia2 = BusquedaPorEspecialidad()

        buscador = Buscador(
            repo=mock_profesional_repository_con_datos, estrategia=estrategia1
        )

        assert buscador.estrategia is estrategia1

        buscador.cambiar_estrategia(estrategia2)

        assert buscador.estrategia is estrategia2

    def test_buscar_ejecuta_estrategia(
        self, mock_profesional_repository_con_datos, profesional_enfermeria
    ):
        """El Buscador ejecuta la estrategia y guarda resultados"""
        estrategia = BusquedaPorEspecialidad()
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos, estrategia=estrategia
        )

        filtro = FiltroBusqueda(nombre_especialidad="Cardiología")

        resultado = buscador.buscar(filtro)

        assert isinstance(resultado, list)
        assert buscador.profesionales == resultado

    def test_buscar_actualiza_profesionales(
        self,
        mock_profesional_repository_con_datos,
        profesional_enfermeria,
    ):
        """Cada búsqueda actualiza la lista de profesionales"""
        estrategia = BusquedaPorEspecialidad()
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos, estrategia=estrategia
        )

        filtro1 = FiltroBusqueda(nombre_especialidad="Cardiología")
        buscador.buscar(filtro1)

        filtro2 = FiltroBusqueda(nombre_especialidad="Dermatología")
        resultado2 = buscador.buscar(filtro2)

        assert buscador.profesionales == resultado2

    def test_cambiar_estrategia_dinamicamente(
        self, mock_profesional_repository_con_datos
    ):
        """Es posible cambiar estrategia durante el uso del Buscador"""
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos,
            estrategia=BusquedaPorZona(),
        )

        filtro_zona = FiltroBusqueda(provincia="Buenos Aires")
        buscador.buscar(filtro_zona)

        buscador.cambiar_estrategia(BusquedaPorEspecialidad())

        filtro_esp = FiltroBusqueda(nombre_especialidad="Cardiología")
        buscador.buscar(filtro_esp)

        assert isinstance(buscador.profesionales, list)

    def test_buscar_con_filtro_vacio_delega_a_estrategia(
        self, mock_profesional_repository_con_datos
    ):
        """El Buscador delega al repositorio que maneja filtros vacíos"""
        estrategia = BusquedaPorEspecialidad()
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos, estrategia=estrategia
        )

        filtro_vacio = FiltroBusqueda()
        mock_profesional_repository_con_datos.buscar_por_especialidad.return_value = []

        resultado = buscador.buscar(filtro_vacio)

        assert resultado == []
        mock_profesional_repository_con_datos.buscar_por_especialidad.assert_called_once()


class TestBuscadorIntegracion:
    """Tests de integración: Buscador + Estrategias"""

    def test_flujo_completo_busqueda_zona(
        self, mock_profesional_repository_con_datos, profesional_enfermeria
    ):
        """Flujo completo: crear buscador, buscar por zona"""
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos,
            estrategia=BusquedaPorZona(),
        )

        filtro = FiltroBusqueda(provincia="Buenos Aires")
        resultados = buscador.buscar(filtro)

        assert isinstance(resultados, list)
        assert buscador.profesionales == resultados

    def test_flujo_completo_busqueda_especialidad(
        self, mock_profesional_repository_con_datos, profesional_enfermeria
    ):
        """Flujo completo: crear buscador, buscar por especialidad"""
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos,
            estrategia=BusquedaPorEspecialidad(),
        )

        filtro = FiltroBusqueda(nombre_especialidad="Cardiología")
        resultados = buscador.buscar(filtro)

        assert isinstance(resultados, list)

    def test_flujo_completo_busqueda_combinada(
        self, mock_profesional_repository_con_datos, profesional_enfermeria
    ):
        """Flujo completo: crear buscador, buscar combinado"""
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos,
            estrategia=BusquedaCombinada(),
        )

        filtro = FiltroBusqueda(
            nombre_especialidad="Cardiología", provincia="Buenos Aires"
        )
        resultados = buscador.buscar(filtro)

        assert isinstance(resultados, list)

    def test_cambio_estrategia_midstream(self, mock_profesional_repository_con_datos):
        """Cambiar estrategia mientras se usa el buscador"""
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos,
            estrategia=BusquedaPorZona(),
        )

        filtro1 = FiltroBusqueda(provincia="Buenos Aires")
        res1 = buscador.buscar(filtro1)

        buscador.cambiar_estrategia(BusquedaPorEspecialidad())

        filtro2 = FiltroBusqueda(nombre_especialidad="Cardiología")
        res2 = buscador.buscar(filtro2)

        assert isinstance(res1, list)
        assert isinstance(res2, list)


class TestBuscadorEdgeCases:
    """Tests para casos edge"""

    def test_multiples_busquedas_consecutivas(
        self, mock_profesional_repository_con_datos
    ):
        """Múltiples búsquedas sin cambiar estrategia"""
        buscador = Buscador(
            repo=mock_profesional_repository_con_datos,
            estrategia=BusquedaPorZona(),
        )

        for _ in range(5):
            filtro = FiltroBusqueda(provincia="Buenos Aires")
            resultado = buscador.buscar(filtro)
            assert isinstance(resultado, list)

    def test_busqueda_sin_resultados(self, mock_profesional_repository):
        """Búsqueda que retorna lista vacía"""
        buscador = Buscador(
            repo=mock_profesional_repository,
            estrategia=BusquedaPorEspecialidad(),
        )

        mock_profesional_repository.buscar_por_especialidad.return_value = []

        filtro = FiltroBusqueda(nombre_especialidad="NoExiste")
        resultado = buscador.buscar(filtro)

        assert resultado == []
        assert buscador.profesionales == []
