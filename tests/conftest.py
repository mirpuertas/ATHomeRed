"""
Fixtures compartidas para tests
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import date, time
from decimal import Decimal

from app.domain.entities.usuarios import (
    Profesional,
    Solicitante,
    Paciente,
)
from app.domain.entities.catalogo import (
    Especialidad,
    Tarifa,
    Publicacion,
    FiltroBusqueda,
)
from app.domain.value_objects.objetos_valor import (
    Ubicacion,
    Disponibilidad,
    Matricula,
)
from app.infra.repositories.profesional_repository import ProfesionalRepository


@pytest.fixture
def ubicacion_buenos_aires():
    """Ubicación en CABA"""
    return Ubicacion(
        provincia="Buenos Aires",
        departamento="CABA",
        barrio="Flores",
        calle="Av. Acoyte",
        numero="1234",
        latitud=-34.6037,
        longitud=-58.3816,
    )


@pytest.fixture
def ubicacion_mendoza():
    """Ubicación en Mendoza"""
    return Ubicacion(
        provincia="Mendoza",
        departamento="Capital",
        barrio="Centro",
        calle="San Martín",
        numero="500",
        latitud=-32.8895,
        longitud=-68.8458,
    )


@pytest.fixture
def ubicacion_cordoba():
    """Ubicación en Córdoba"""
    return Ubicacion(
        provincia="Córdoba",
        departamento="Capital",
        barrio="Centro",
        calle="Av. Colón",
        numero="800",
        latitud=-31.4201,
        longitud=-64.1888,
    )


@pytest.fixture
def especialidad_enfermeria():
    """Especialidad: Enfermería (servicio principal de ATHomeRed)"""
    return Especialidad(id=1, nombre="Enfermería", tarifa=Decimal("2500.00"))


@pytest.fixture
def especialidad_acompanante():
    """Especialidad: Acompañante Terapéutico (servicio principal de ATHomeRed)"""
    return Especialidad(
        id=2, nombre="Acompañante Terapéutico", tarifa=Decimal("2000.00")
    )


@pytest.fixture
def especialidad_geriatria():
    """Especialidad: Geriatría (atención a adultos mayores)"""
    return Especialidad(id=3, nombre="Geriatría", tarifa=Decimal("2800.00"))


@pytest.fixture
def disponibilidad_lunes_manana():
    """Disponibilidad: Lunes 9:00 a 13:00"""
    from app.domain.enumeraciones import DiaSemana

    return Disponibilidad(
        dias_semana=[DiaSemana.LUNES],
        hora_inicio=time(9, 0),
        hora_fin=time(13, 0),
    )


@pytest.fixture
def disponibilidad_miercoles_tarde():
    """Disponibilidad: Miércoles 14:00 a 18:00"""
    from app.domain.enumeraciones import DiaSemana

    return Disponibilidad(
        dias_semana=[DiaSemana.MIERCOLES],
        hora_inicio=time(14, 0),
        hora_fin=time(18, 0),
    )


@pytest.fixture
def matricula_buenos_aires():
    """Matrícula en Buenos Aires"""
    from datetime import date

    return Matricula(
        numero="123456",
        provincia="Buenos Aires",
        vigente_desde=date(2020, 1, 1),
        vigente_hasta=date(2030, 12, 31),
    )


@pytest.fixture
def matricula_mendoza():
    """Matrícula en Mendoza"""
    from datetime import date

    return Matricula(
        numero="789012",
        provincia="Mendoza",
        vigente_desde=date(2021, 1, 1),
        vigente_hasta=date(2031, 12, 31),
    )


@pytest.fixture
def profesional_enfermeria(
    ubicacion_buenos_aires,
    especialidad_enfermeria,
    disponibilidad_lunes_manana,
    matricula_buenos_aires,
):
    """Profesional de Enfermería (ATHomeRed)"""
    prof = Profesional(
        id=uuid4(),
        nombre="Ana",
        apellido="López",
        email="ana.lopez@athomered.com",
        celular="1123456789",
        ubicacion=ubicacion_buenos_aires,
        verificado=True,
        especialidades=[especialidad_enfermeria],
        disponibilidades=[disponibilidad_lunes_manana],
        matriculas=[matricula_buenos_aires],
    )
    return prof


@pytest.fixture
def profesional_acompanante(
    ubicacion_mendoza,
    especialidad_acompanante,
    disponibilidad_miercoles_tarde,
    matricula_mendoza,
):
    """Acompañante Terapéutico (ATHomeRed)"""
    prof = Profesional(
        id=uuid4(),
        nombre="Carlos",
        apellido="Fernández",
        email="carlos.fernandez@athomered.com",
        celular="2614567890",
        ubicacion=ubicacion_mendoza,
        verificado=True,
        especialidades=[especialidad_acompanante],
        disponibilidades=[disponibilidad_miercoles_tarde],
        matriculas=[matricula_mendoza],
    )
    return prof


@pytest.fixture
def solicitante(ubicacion_buenos_aires):
    """Solicitante que gestiona turnos"""
    return Solicitante(
        id=uuid4(),
        nombre="Carlos",
        apellido="López",
        email="carlos.lopez@example.com",
        celular="1187654321",
        ubicacion=ubicacion_buenos_aires,
        activo=True,
    )


@pytest.fixture
def solicitante_mendoza(ubicacion_mendoza):
    """Solicitante en Mendoza"""
    return Solicitante(
        id=uuid4(),
        nombre="Ana",
        apellido="Martínez",
        email="ana.martinez@example.com",
        celular="2612345678",
        ubicacion=ubicacion_mendoza,
        activo=True,
    )


@pytest.fixture
def paciente(solicitante):
    """Paciente de 45 años"""
    paciente = Paciente(
        id=uuid4(),
        nombre="Roberto",
        apellido="Fernández",
        fecha_nacimiento=date(1979, 5, 15),
        ubicacion=solicitante.ubicacion,
        solicitante_id=solicitante.id,
        relacion="self",
    )
    solicitante.agregar_paciente(paciente)
    return paciente


@pytest.fixture
def paciente_hijo(solicitante):
    """Paciente hijo de 12 años"""
    paciente = Paciente(
        id=uuid4(),
        nombre="Lucas",
        apellido="López",
        fecha_nacimiento=date(2012, 8, 20),
        ubicacion=solicitante.ubicacion,
        solicitante_id=solicitante.id,
        relacion="hijo",
    )
    solicitante.agregar_paciente(paciente)
    return paciente


@pytest.fixture
def filtro_enfermeria_buenos_aires():
    """Filtro: Enfermería en Buenos Aires (ATHomeRed)"""
    return FiltroBusqueda(
        nombre_especialidad="Enfermería",
        provincia="Buenos Aires",
    )


@pytest.fixture
def filtro_solo_enfermeria():
    """Filtro: Solo especialidad Enfermería"""
    return FiltroBusqueda(
        nombre_especialidad="Enfermería",
    )


@pytest.fixture
def filtro_solo_provincia():
    """Filtro: Solo provincia Buenos Aires"""
    return FiltroBusqueda(
        provincia="Buenos Aires",
    )


@pytest.fixture
def filtro_acompanante_mendoza():
    """Filtro: Acompañante Terapéutico en Mendoza (ATHomeRed)"""
    return FiltroBusqueda(
        nombre_especialidad="Acompañante Terapéutico",
        provincia="Mendoza",
    )


@pytest.fixture
def mock_profesional_repository():
    """Mock del ProfesionalRepository"""
    mock = MagicMock(spec=ProfesionalRepository)
    return mock


@pytest.fixture
def mock_profesional_repository_con_datos(
    profesional_enfermeria,
    profesional_acompanante,
):
    """Mock del repositorio con datos precargados (ATHomeRed)"""
    mock = MagicMock(spec=ProfesionalRepository)

    def mock_buscar_por_especialidad(especialidad_id=None, especialidad_nombre=None):
        if especialidad_id == 1 or especialidad_nombre == "Enfermería":
            return [profesional_enfermeria]
        elif especialidad_id == 2 or especialidad_nombre == "Acompañante Terapéutico":
            return [profesional_acompanante]
        return []

    mock.buscar_por_especialidad.side_effect = mock_buscar_por_especialidad

    mock.buscar_por_ubicacion.side_effect = (
        lambda provincia=None, departamento=None, barrio=None: (
            [profesional_enfermeria]
            if provincia == "Buenos Aires"
            else [profesional_acompanante]
            if provincia == "Mendoza"
            else []
        )
    )

    def mock_buscar_combinado(
        especialidad_id=None,
        especialidad_nombre=None,
        provincia=None,
        departamento=None,
        barrio=None,
    ):
        es_enfermeria = especialidad_id == 1 or especialidad_nombre == "Enfermería"
        es_acompanante = (
            especialidad_id == 2 or especialidad_nombre == "Acompañante Terapéutico"
        )

        if es_enfermeria and provincia == "Buenos Aires":
            return [profesional_enfermeria]
        elif es_acompanante and provincia == "Mendoza":
            return [profesional_acompanante]
        return []

    mock.buscar_combinado.side_effect = mock_buscar_combinado

    return mock


@pytest.fixture
def tarifa_enfermeria():
    """Tarifa para Enfermería (ATHomeRed)"""
    return Tarifa(
        id=1,
        id_especialidad=1,
        monto=Decimal("2500.00"),
        vigente_desde=date(2024, 1, 1),
        vigente_hasta=date(2024, 12, 31),
    )


@pytest.fixture
def publicacion_enfermeria(profesional_enfermeria, especialidad_enfermeria):
    """Publicación de un profesional de enfermería"""
    return Publicacion(
        id=1,
        id_profesional=str(profesional_enfermeria.id),
        titulo="Servicios de Enfermería a Domicilio",
        descripcion="Atención integral de enfermería profesional en el hogar",
        especialidades=[especialidad_enfermeria],
    )
