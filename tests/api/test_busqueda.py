"""
Tests de integración para el endpoint de búsqueda de profesionales
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from uuid import uuid4

from app.main import app
from app.api.dependencies import (
    get_profesional_repository,
    get_catalogo_repository,
    get_direccion_repository,
)


@pytest.fixture
def client():
    """Cliente para hacer requests HTTP a la API"""
    return TestClient(app)


@pytest.fixture
def mock_repos(profesional_enfermeria, especialidad_enfermeria, ubicacion_buenos_aires):
    """Fixture que configura mocks de repositorios (ATHomeRed)"""
    mock_prof_repo = Mock()
    mock_catalogo_repo = Mock()
    mock_dir_repo = Mock()

    especialidad_mock = Mock()
    especialidad_mock.id = 1
    especialidad_mock.nombre = "Enfermería"

    provincia_mock = Mock()
    provincia_mock.id = uuid4()
    provincia_mock.nombre = "Buenos Aires"

    mock_catalogo_repo.obtener_especialidad_por_nombre.return_value = especialidad_mock
    mock_catalogo_repo.obtener_especialidad_por_id.return_value = especialidad_mock
    mock_catalogo_repo.listar_especialidades.return_value = [especialidad_mock]

    mock_prof_repo.buscar_por_especialidad.return_value = [profesional_enfermeria]
    mock_prof_repo.buscar_por_ubicacion.return_value = [profesional_enfermeria]
    mock_prof_repo.buscar_combinado.return_value = [profesional_enfermeria]

    mock_dir_repo.listar_provincias.return_value = [provincia_mock]

    app.dependency_overrides[get_profesional_repository] = lambda: mock_prof_repo
    app.dependency_overrides[get_catalogo_repository] = lambda: mock_catalogo_repo
    app.dependency_overrides[get_direccion_repository] = lambda: mock_dir_repo

    yield {
        "profesional": mock_prof_repo,
        "catalogo": mock_catalogo_repo,
        "direccion": mock_dir_repo,
    }

    app.dependency_overrides.clear()


class TestBusquedaProfesionalesEndpoint:
    """Tests para POST /busqueda/profesionales"""

    def test_busqueda_sin_criterios(self, client, mock_repos):
        """Debe rechazar búsqueda sin criterios"""
        response = client.post("/busqueda/profesionales", json={})

        assert response.status_code in [400, 422]

    def test_busqueda_departamento_sin_provincia(self, client, mock_repos):
        """Debe rechazar departamento sin provincia"""
        payload = {"departamento": "CABA"}

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code in [400, 422]

    def test_busqueda_barrio_sin_departamento(self, client, mock_repos):
        """Debe rechazar barrio sin departamento"""
        payload = {"provincia": "Buenos Aires", "barrio": "Flores"}

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code in [400, 422]

    def test_busqueda_especialidad_no_existe(self, client, mock_repos):
        """Debe retornar 404 si la especialidad no existe"""
        mock_repos["catalogo"].obtener_especialidad_por_nombre.return_value = None

        payload = {"nombre_especialidad": "EspecialidadQueNoExiste"}

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 404

    def test_busqueda_por_especialidad_exitosa(self, client, mock_repos):
        """Búsqueda por especialidad debe retornar resultados"""
        payload = {"nombre_especialidad": "Cardiología"}

        response = client.post("/busqueda/profesionales", json=payload)

        if response.status_code != 200:
            print(f"ERROR: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "profesionales" in data
        assert "total" in data
        assert data["total"] >= 0

    def test_busqueda_por_zona_exitosa(self, client, mock_repos):
        """Búsqueda por zona debe retornar resultados"""
        payload = {"provincia": "Buenos Aires"}

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "profesionales" in data
        assert data["total"] >= 0

    def test_busqueda_combinada_exitosa(self, client, mock_repos):
        """Búsqueda combinada debe usar estrategia correcta"""
        payload = {
            "nombre_especialidad": "Cardiología",
            "provincia": "Buenos Aires",
        }

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "profesionales" in data
        mock_repos["profesional"].buscar_combinado.assert_called_once()

    def test_busqueda_completa_con_jerarquia(self, client, mock_repos):
        """Búsqueda con provincia, departamento y barrio"""
        payload = {
            "nombre_especialidad": "Cardiología",
            "provincia": "Buenos Aires",
            "departamento": "CABA",
            "barrio": "Flores",
        }

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 200

    def test_busqueda_retorna_lista_vacia(self, client, mock_repos):
        """Búsqueda sin resultados debe retornar lista vacía"""
        mock_repos["profesional"].buscar_por_especialidad.return_value = []

        payload = {"nombre_especialidad": "Cardiología"}

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["profesionales"] == []


class TestEspecialidadesEndpoint:
    """Tests para GET /busqueda/especialidades"""

    def test_listar_especialidades(self, client, mock_repos):
        """Debe listar todas las especialidades"""
        response = client.get("/busqueda/especialidades")

        assert response.status_code == 200
        data = response.json()
        assert "especialidades" in data
        assert len(data["especialidades"]) >= 0

    def test_listar_especialidades_vacio(self, client, mock_repos):
        """Sin especialidades debe retornar lista vacía"""
        mock_repos["catalogo"].listar_especialidades.return_value = []

        response = client.get("/busqueda/especialidades")

        assert response.status_code == 200
        data = response.json()
        assert data["especialidades"] == []


class TestProvinciasEndpoint:
    """Tests para GET /busqueda/ubicaciones/provincias"""

    def test_listar_provincias(self, client, mock_repos):
        """Debe listar todas las provincias"""
        response = client.get("/busqueda/ubicaciones/provincias")

        assert response.status_code == 200
        data = response.json()
        assert "provincias" in data
        assert len(data["provincias"]) >= 0

    def test_listar_provincias_vacio(self, client, mock_repos):
        """Sin provincias debe retornar lista vacía"""
        mock_repos["direccion"].listar_provincias.return_value = []

        response = client.get("/busqueda/ubicaciones/provincias")

        assert response.status_code == 200
        data = response.json()
        assert data["provincias"] == []


class TestBusquedaErrores:
    """Tests de manejo de errores"""

    def test_error_interno_manejado(self, client, mock_repos):
        """Errores internos deben retornar 500"""
        mock_repos["profesional"].buscar_por_especialidad.side_effect = Exception(
            "Error BD"
        )

        payload = {"nombre_especialidad": "Cardiología"}

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()

    def test_valor_error_retorna_400(self, client, mock_repos):
        """ValueError debe retornar 400"""
        mock_repos["profesional"].buscar_por_especialidad.side_effect = ValueError(
            "Filtro inválido"
        )

        payload = {"nombre_especialidad": "Cardiología"}

        response = client.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 400
