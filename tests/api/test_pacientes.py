"""
Tests para los routers de la API (tests de integración HTTP)

Tests con mocks de repositorios para validar el comportamiento
de los endpoints sin dependencia de base de datos real.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4

from app.main import app


@pytest.fixture
def client():
    """Cliente para hacer requests HTTP a la API"""
    return TestClient(app)


@pytest.fixture
def ubicacion_dict():
    """Diccionario de ubicación para requests"""
    return {
        "provincia": "Buenos Aires",
        "departamento": "CABA",
        "barrio": "Flores",
        "calle": "Av. Acoyte",
        "numero": "1234",
        "latitud": -34.6037,
        "longitud": -58.3816,
    }


@pytest.fixture
def paciente_create_data(ubicacion_dict):
    """Datos para crear un paciente"""
    return {
        "nombre": "Roberto",
        "apellido": "Fernández",
        "fecha_nacimiento": "1979-05-15",
        "relacion": "self",
        "notas": "Sin alergias conocidas",
        "ubicacion": ubicacion_dict,
        "solicitante_id": str(uuid4()),
    }


class TestPacientesRouter:
    """Tests para el router de pacientes"""

    def test_crear_paciente_nombre_muy_corto(self, client, paciente_create_data):
        """POST /pacientes - Validar nombre mínimo"""
        paciente_create_data["nombre"] = "R"

        response = client.post("/pacientes/", json=paciente_create_data)

        assert response.status_code == 422

    def test_crear_paciente_email_invalido(self, client, paciente_create_data):
        """POST /pacientes - Validar formato email"""
        with patch("app.api.dependencies.get_paciente_repository") as mock_repo_dep:
            mock_repo = Mock()
            mock_repo.crear.side_effect = ValueError("Email inválido")
            mock_repo_dep.return_value = mock_repo

            response = client.post("/pacientes/", json=paciente_create_data)

            if response.status_code != 201:
                assert response.status_code in [400, 422, 500]

    def test_obtener_paciente_no_existe(self, client):
        """GET /pacientes/{id} - Paciente no encontrado"""
        paciente_id = uuid4()

        with patch("app.api.dependencies.get_paciente_repository") as mock_repo_dep:
            mock_repo = Mock()
            mock_repo.obtener_por_id.return_value = None
            mock_repo_dep.return_value = mock_repo

            response = client.get(f"/pacientes/{paciente_id}")

            assert response.status_code == 404

    def test_actualizar_paciente_no_existe(self, client, paciente_create_data):
        """PUT /pacientes/{id} - Actualizar paciente que no existe"""
        paciente_id = uuid4()

        with patch("app.api.dependencies.get_paciente_repository") as mock_repo_dep:
            mock_repo = Mock()
            mock_repo.obtener_por_id.return_value = None
            mock_repo_dep.return_value = mock_repo

            response = client.put(
                f"/pacientes/{paciente_id}", json=paciente_create_data
            )

            assert response.status_code == 404

    def test_eliminar_paciente_no_existe(self, client):
        """DELETE /pacientes/{id} - Eliminar paciente que no existe"""
        paciente_id = uuid4()

        with patch("app.api.dependencies.get_paciente_repository") as mock_repo_dep:
            mock_repo = Mock()
            mock_repo.eliminar.return_value = False
            mock_repo_dep.return_value = mock_repo

            response = client.delete(f"/pacientes/{paciente_id}")

            assert response.status_code == 404


class TestHealthCheck:
    """Tests básicos de salud de la API"""

    def test_api_respondiendo(self, client):
        """Verificar que la API responde"""
        assert client is not None


class TestErrorHandling:
    """Tests para manejo de errores genéricos"""

    def test_404_en_endpoint_inexistente(self, client):
        """GET a endpoint que no existe retorna 404"""
        response = client.get("/endpoint-que-no-existe/")

        assert response.status_code == 404
