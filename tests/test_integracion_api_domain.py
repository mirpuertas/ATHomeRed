"""
Test de integración: Verificar que API y Domain funcionan juntos
Los tests verifican que las capas se integran sin errores de import/estructura.
"""

from datetime import date, time

from app.domain.entities.usuarios import Profesional
from app.api.routers import busqueda
from app.domain.value_objects.objetos_valor import (
    Ubicacion,
    Disponibilidad,
    Matricula,
)
from app.domain.enumeraciones import DiaSemana
from uuid import uuid4

from app.api.routers.busqueda import (
    Buscador,
    BusquedaPorZona,
    BusquedaPorEspecialidad,
    BusquedaCombinada,
)


class TestIntegracionAPIaDomain:
    """Tests de integración entre API y Domain"""

    def test_domain_strategies_importan_correctamente(self):
        """Verifica que se pueden importar las estrategias del domain desde la API"""
        assert Buscador is not None
        assert BusquedaPorZona is not None
        assert BusquedaPorEspecialidad is not None
        assert BusquedaCombinada is not None

    def test_domain_entities_se_usan_en_api(self):
        """Verifica que las entidades del domain se usan en API sin problemas"""
        ubicacion = Ubicacion(
            provincia="Buenos Aires",
            departamento="CABA",
            barrio="Flores",
            calle="Av. Acoyte",
            numero="1234",
        )

        prof = Profesional(
            id=uuid4(),
            nombre="Juan",
            apellido="Pérez",
            email="juan@example.com",
            celular="1234567890",
            ubicacion=ubicacion,
            verificado=True,
        )

        assert prof.nombre_completo == "Juan Pérez"
        assert prof.verificado is True
        assert prof.ubicacion.provincia == "Buenos Aires"

    def test_domain_value_objects_funcionan_correctamente(self):
        """Verifica que los value objects del domain funcionan correctamente"""
        ubicacion = Ubicacion(
            provincia="Buenos Aires",
            departamento="CABA",
            barrio="Flores",
            calle="Av. Acoyte",
            numero="1234",
        )

        disponibilidad = Disponibilidad(
            dias_semana=[DiaSemana.LUNES, DiaSemana.MIERCOLES],
            hora_inicio=time(9, 0),
            hora_fin=time(13, 0),
        )

        matricula = Matricula(
            numero="123456",
            provincia="Buenos Aires",
            vigente_desde=date(2020, 1, 1),
            vigente_hasta=date(2030, 12, 31),
        )

        prof = Profesional(
            id=uuid4(),
            nombre="Juan",
            apellido="Pérez",
            email="juan@example.com",
            celular="1234567890",
            ubicacion=ubicacion,
            disponibilidades=[disponibilidad],
            matriculas=[matricula],
            verificado=True,
        )

        assert prof.nombre_completo == "Juan Pérez"
        assert prof.verificado is True
        assert len(prof.disponibilidades) == 1
        assert len(prof.matriculas) == 1
        assert prof.matriculas[0].provincia == "Buenos Aires"
        assert prof.disponibilidades[0].hora_inicio == time(9, 0)

    def test_api_router_importa_domain_correctamente(self):
        """Verifica que el router de búsqueda importa estrategias del domain sin errores"""

        assert hasattr(busqueda, "router")
        assert hasattr(busqueda, "Buscador")
        assert hasattr(busqueda, "BusquedaPorZona")
        assert hasattr(busqueda, "FiltroBusqueda")
