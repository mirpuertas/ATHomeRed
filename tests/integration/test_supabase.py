"""
Tests de integración con Supabase
Usa tu instancia de Supabase con transacciones rollback
"""

import pytest
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_db

from app.infra.persistence.servicios import EspecialidadORM
from app.infra.persistence.ubicacion import (
    ProvinciaORM,
    DepartamentoORM,
    BarrioORM,
)
from uuid import uuid4


def get_supabase_test_url():
    """
    Obtiene URL de Supabase desde variables de entorno

    Opción 1: Usar misma BD de desarrollo (con rollback)
    Opción 2: Crear proyecto Supabase separado para tests
    """
    supabase_url = os.getenv("SUPABASE_DB_URL")
    if not supabase_url:
        pytest.skip("SUPABASE_DB_URL no configurado en .env")
    return supabase_url


@pytest.fixture(scope="session")
def supabase_engine():
    """
    Engine de Supabase para tests
    Scope session = se crea una vez por sesión de tests
    """
    db_url = get_supabase_test_url()

    engine = create_engine(db_url, poolclass=NullPool, echo=False)

    yield engine

    engine.dispose()


@pytest.fixture(scope="function")
def db_session_supabase(supabase_engine):
    """
    Sesión con rollback automático

    VENTAJA: Cada test corre en una transacción que se deshace al final
    La BD de Supabase queda limpia, sin basura de tests
    """
    connection = supabase_engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)

    connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.expire_all()
            session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client_supabase(db_session_supabase):
    """
    Cliente de test con Supabase
    Override de la dependencia get_db
    """

    def override_get_db():
        try:
            yield db_session_supabase
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def seed_supabase_data(db_session_supabase):
    """
    Carga datos de prueba en Supabase
    Se hace rollback automáticamente después del test
    """
    provincia = ProvinciaORM(id=str(uuid4()), nombre="Buenos Aires Test")
    db_session_supabase.add(provincia)
    db_session_supabase.flush()

    departamento = DepartamentoORM(
        id=str(uuid4()), nombre="CABA Test", provincia_id=provincia.id
    )
    db_session_supabase.add(departamento)
    db_session_supabase.flush()

    barrio = BarrioORM(
        id=str(uuid4()), nombre="Flores Test", departamento_id=departamento.id
    )
    db_session_supabase.add(barrio)

    especialidad = EspecialidadORM(
        id_especialidad=999,
        nombre="Test Cardiología",
        descripcion="Especialidad de prueba para tests",
        tarifa=5000.00,
    )
    db_session_supabase.add(especialidad)

    db_session_supabase.commit()

    return {
        "provincia": provincia,
        "departamento": departamento,
        "barrio": barrio,
        "especialidad": especialidad,
    }


class TestIntegracionSupabase:
    """
    Tests de integración con Supabase (PostgreSQL)
    Marcar con @pytest.mark.supabase
    """

    @pytest.mark.integration
    @pytest.mark.supabase
    def test_listar_especialidades_supabase(self, client_supabase):
        """
        Test real contra Supabase
        Usa datos que ya existen en tu BD
        """
        response = client_supabase.get("/busqueda/especialidades")

        assert response.status_code == 200
        data = response.json()
        assert "especialidades" in data

    @pytest.mark.integration
    @pytest.mark.supabase
    def test_listar_provincias_supabase(self, client_supabase):
        """Test con datos reales de Supabase"""
        response = client_supabase.get("/busqueda/ubicaciones/provincias")

        assert response.status_code == 200
        data = response.json()
        assert "provincias" in data

    @pytest.mark.integration
    @pytest.mark.supabase
    def test_busqueda_profesionales_con_datos_seed(
        self, client_supabase, seed_supabase_data
    ):
        """
        Test con datos de prueba que se eliminan automáticamente
        """
        payload = {"nombre_especialidad": "Test Cardiología"}

        response = client_supabase.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "profesionales" in data
        assert data["total"] >= 0

    @pytest.mark.integration
    @pytest.mark.supabase
    def test_joins_corregidos_en_supabase(self, client_supabase, seed_supabase_data):
        """
        Verifica que la corrección de joins duplicados funcione en Supabase
        Este test fallaría con la versión antigua
        """
        payload = {
            "nombre_especialidad": "Test Cardiología",
            "provincia": "Buenos Aires Test",
            "departamento": "CABA Test",
        }

        response = client_supabase.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 200


class TestSupabaseConDatosReales:
    """
    Tests que usan datos reales de tu BD Supabase
    SIN rollback - solo lectura
    """

    @pytest.mark.integration
    @pytest.mark.supabase
    @pytest.mark.readonly
    def test_contar_especialidades_reales(self, client_supabase):
        """Verifica que hay especialidades en la BD real"""
        response = client_supabase.get("/busqueda/especialidades")

        assert response.status_code == 200
        data = response.json()

        if len(data["especialidades"]) == 0:
            pytest.skip("BD sin especialidades - ejecutar seed primero")

    @pytest.mark.integration
    @pytest.mark.supabase
    @pytest.mark.readonly
    def test_buscar_profesionales_reales(self, client_supabase):
        """
        Busca profesionales que existen en tu BD
        Ajusta la especialidad según tus datos
        """
        response = client_supabase.get("/busqueda/especialidades")
        especialidades = response.json()["especialidades"]

        if not especialidades:
            pytest.skip("No hay especialidades en BD")

        primera_especialidad = especialidades[0]["nombre"]

        payload = {"nombre_especialidad": primera_especialidad}

        response = client_supabase.post("/busqueda/profesionales", json=payload)

        assert response.status_code == 200
