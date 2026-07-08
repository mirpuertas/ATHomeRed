"""
Tests de autenticación (mínimos) usando FastAPI + TestClient con SQLite en
memoria. Se evita Postgres/Alembic para que estos tests sean rápidos y
autocontenidos.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.dependencies import get_db
from tests.api.auth_minimal_models import Base, UsuarioORM, RefreshTokenORM

from app.services import auth_service
from app.infra.repositories import usuario_repository
import app.api.routers.auth as auth_router_mod

from sqlalchemy.orm import Session

from datetime import timedelta
from app.services.auth_service import AuthService


def _setup_sqlite_memory():
    """
    Configura una base SQLite en memoria compartida (StaticPool) y prepara
    una `SessionLocal` para usar en los tests.

    - Fuerza un secreto predecible (`AT_HOME_RED_SECRET`) para tokens.
    - Crea las tablas mínimas requeridas por el flujo de auth sobre `Base`.

    Returns
    -------
    (sessionmaker, Engine)
        Un `sessionmaker` enlazado al engine en memoria y el engine creado.
    """
    os.environ.setdefault("AT_HOME_RED_SECRET", "testing-secret")

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal, engine


class FakeUsuarioRepository:
    """
    Repositorio falso de usuarios para los tests de auth.

    Usa directamente el ORM mínimo del módulo de pruebas (`UsuarioORM`) sobre
    la sesión SQLite en memoria. Implementa lo necesario para:
    - buscar por email / id,
    - crear usuario,
    - banderitas básicas de seguridad (bloqueo/intentoss), sin lógica real.
    """

    def __init__(self, db):
        """Guarda la sesión de DB de prueba."""
        self.db = db

    def obtener_por_email(self, email):
        """Devuelve el usuario con ese email o None si no existe."""
        return self.db.query(UsuarioORM).filter_by(email=email).first()

    def crear_usuario(self, **kwargs):
        """
        Crea un `UsuarioORM` garantizando que el `id` sea string (UUID str).
        Commit + refresh para devolver el objeto persistido.
        """
        import uuid

        if "id" not in kwargs or kwargs["id"] is None:
            kwargs["id"] = str(uuid.uuid4())
        else:
            kwargs["id"] = str(kwargs["id"])
        user = UsuarioORM(**kwargs)
        print(f"[DEBUG] crear_usuario: creando usuario id={user.id} email={user.email}")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def actualizar_ultimo_login(self, usuario_id):
        """Actualiza (dummy) el `ultimo_login` del usuario con ese id."""
        user = self.obtener_por_id(usuario_id)
        if user:
            user.ultimo_login = None
            self.db.commit()

    def incrementar_intentos_fallidos(self, email):
        """No-op: incrementos de intentos fallidos deshabilitados en el fake."""
        return 0

    def resetear_intentos_fallidos(self, usuario_id):
        """No-op: reseteo de intentos fallidos deshabilitado en el fake."""
        return True

    def esta_bloqueado(self, email):
        """Siempre devuelve False en este fake (no hay bloqueo real)."""
        return False

    def obtener_por_id(self, usuario_id):
        """
        Busca usuario por id (comparando como string).
        Loguea ids presentes para facilitar debugging del test.
        """
        all_ids = [str(u.id) for u in self.db.query(UsuarioORM).all()]
        print(
            f"[DEBUG] obtener_por_id: buscando id={usuario_id} "
            f"(str={str(usuario_id)}), en DB: {all_ids}"
        )
        return (
            self.db.query(UsuarioORM).filter(UsuarioORM.id == str(usuario_id)).first()
        )


class FakeAuthRepository:
    """
    Repositorio falso para refresh-tokens.

    Provee crear/obtener/revocar tokens sobre `RefreshTokenORM`, haciendo
    commits inmediatos (simplifica el flujo del test).
    """

    def __init__(self, db):
        """Guarda la sesión de DB de prueba."""
        self.db = db

    def crear_refresh_token(self, **kwargs):
        """Crea y persiste un `RefreshTokenORM`."""
        token = RefreshTokenORM(**kwargs)
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def obtener_refresh_token(self, token):
        """Devuelve un token activo (no revocado) o None."""
        return (
            self.db.query(RefreshTokenORM)
            .filter_by(token=token, revocado=False)
            .first()
        )

    def revocar_refresh_token(self, token):
        """Marca un token como revocado; True si lo encontró y revocó."""
        t = self.db.query(RefreshTokenORM).filter_by(token=token).first()
        if t:
            t.revocado = True
            self.db.commit()
            return True
        return False

    def revocar_todos_tokens_usuario(self, usuario_id):
        """Revoca todos los tokens activos del usuario y devuelve cuántos fueron."""
        tokens = (
            self.db.query(RefreshTokenORM)
            .filter_by(usuario_id=usuario_id, revocado=False)
            .all()
        )
        for t in tokens:
            t.revocado = True
        self.db.commit()
        return len(tokens)

    def registrar_intento_login(self, **kwargs):
        """No-op: en el fake no persistimos intentos de login."""
        pass


class FakeRefreshTokenRepository:
    """
    Variante mínima de repositorio de refresh-tokens.

    Expone crear/obtener/revocar, usada en algunos flujos; se deja separada
    por claridad, aunque el test usa principalmente `FakeAuthRepository`.
    """

    def __init__(self, db):
        """Guarda la sesión de DB de prueba."""
        self.db = db

    def crear(self, **kwargs):
        """Crea y persiste un `RefreshTokenORM` (alias de `crear_refresh_token`)."""
        token = RefreshTokenORM(**kwargs)
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def obtener_por_token(self, token):
        """Devuelve el token (revocado o no) o None."""
        return self.db.query(RefreshTokenORM).filter_by(token=token).first()

    def revocar(self, token):
        """Marca el token como revocado si existe."""
        t = self.db.query(RefreshTokenORM).filter_by(token=token).first()
        if t:
            t.revocado = True
            self.db.commit()


@pytest.fixture(scope="function")
def client_auth():
    """
    Fixture de cliente HTTP para el flujo de auth.

    - Crea el engine SQLite en memoria y su `SessionLocal`.
    - Overrida `get_db` para inyectar esa sesión a los endpoints.
    - Parchea (temporalmente) `AuthService` y `UsuarioRepository` para usar
      los fakes definidos arriba.
    - Devuelve un `TestClient(app)` con todo lo anterior activo.

    Al finalizar, se limpian overrides y se restauran clases originales.
    """
    TestingSessionLocal, engine = _setup_sqlite_memory()

    def override_get_db():
        """Dependency override: entrega una sesión SQLite in-memory."""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    orig_init = auth_service.AuthService.__init__
    orig_repo = usuario_repository.UsuarioRepository
    orig_router_repo = getattr(auth_router_mod, "UsuarioRepository", None)

    def fake_init(self, db):
        """Ctor falso de AuthService: inyecta repos fakes y la sesión de prueba."""
        self.db = db
        self.usuario_repo = FakeUsuarioRepository(db)
        self.auth_repo = FakeAuthRepository(db)

    auth_service.AuthService.__init__ = fake_init
    usuario_repository.UsuarioRepository = FakeUsuarioRepository
    auth_router_mod.UsuarioRepository = FakeUsuarioRepository
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        auth_service.AuthService.__init__ = orig_init
        usuario_repository.UsuarioRepository = orig_repo
        if orig_router_repo is not None:
            auth_router_mod.UsuarioRepository = orig_router_repo


@pytest.mark.authflow
@pytest.mark.auth_ok
def test_login_registro(client_auth: TestClient):
    """
    Test principal de autenticación mínima (end-to-end):

    1) Registro de usuario con `/auth/register-json`.
    2) Login con `/auth/login` y verificación de `access_token` + `refresh_token`.
    3) Consulta de `/auth/me` con header `Authorization: Bearer ...`.
    4) Refresh de access con `/auth/refresh`.

    Este test valida que:
    - Se pueda registrar y loguear un usuario.
    - Se emitan correctamente tokens de acceso y refresh.
    - El endpoint protegido reconozca el Bearer token.
    - El endpoint de refresh devuelva un nuevo access token.
    """
    r = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "tester@probando.com",
            "password": "Prueba123!",
            "nombre": "Tester",
            "apellido": "Probando",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    print("[TEST] Registro status:", r.status_code, r.text)
    assert r.status_code in (200, 201), r.text
    body_reg = r.json()
    print("[TEST] Usuario registrado:", body_reg)
    assert body_reg["email"] == "tester@probando.com"

    r = client_auth.post(
        "/api/v1/auth/login",
        json={"email": "tester@probando.com", "password": "Prueba123!"},
    )
    print("[TEST] Login status:", r.status_code, r.text)
    assert r.status_code == 200, r.text
    tok = r.json()
    print("[TEST] Tokens:", tok)
    assert "access_token" in tok and "refresh_token" in tok

    r = client_auth.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tok['access_token']}"},
    )
    print("[TEST] /me status:", r.status_code, r.text)
    assert r.status_code == 200, r.text
    me = r.json()
    print("[TEST] /me usuario:", me)
    assert me["email"] == "tester@probando.com"

    r = client_auth.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tok["refresh_token"]},
    )
    print("[TEST] Refresh status:", r.status_code, r.text)
    assert r.status_code == 200, r.text
    tok2 = r.json()
    print("[TEST] Nuevo access_token:", tok2)
    assert "access_token" in tok2

    db: Session = next(app.dependency_overrides[get_db]())
    usuarios = db.query(UsuarioORM).all()
    print("[TEST] Usuarios en la DB de test:")
    for u in usuarios:
        print(f"  id={u.id} email={u.email} nombre={u.nombre} activo={u.activo}")


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_login_password_incorrecta(client_auth: TestClient):
    """
    Caso negativo: password inválida.
    - Se registra un usuario válido.
    - Se intenta loguear con password incorrecta.
    - Debe responder 401 (no autorizado).
    """
    r = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "wrongpass@probando.com",
            "password": "Correcta123!",
            "nombre": "Wrong",
            "apellido": "Pass",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    assert r.status_code in (200, 201), r.text

    r = client_auth.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@probando.com", "password": "Incorrecta!"},
    )
    assert r.status_code == 401, r.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_me_sin_autorizacion(client_auth: TestClient):
    """
    Caso negativo: acceso a /me sin header Authorization.
    - GET /auth/me sin Bearer token.
    - Debe responder 401 (no autorizado).
    """
    r = client_auth.get("/api/v1/auth/me")
    assert r.status_code == 401, r.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_refresh_token_invalido(client_auth: TestClient):
    """
    Caso negativo: refresh con token inválido.
    - Se registra y loguea un usuario (para asegurar wiring de dependencias).
    - Se invoca /auth/refresh con un refresh_token inexistente.
    - Debe responder 401.
    """
    r = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "refreshbad@probando.com",
            "password": "Prueba123!",
            "nombre": "Refresh",
            "apellido": "Bad",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    assert r.status_code in (200, 201), r.text

    r = client_auth.post(
        "/api/v1/auth/login",
        json={"email": "refreshbad@probando.com", "password": "Prueba123!"},
    )
    assert r.status_code == 200, r.text

    r = client_auth.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "token-que-no-existe"},
    )
    assert r.status_code == 401, r.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_me_bearer_malformado(client_auth: TestClient):
    """
    Caso negativo: Bearer token malformado en /me.
    - Se registra y loguea un usuario para garantizar que el flujo esté OK.
    - Se llama a /me con 'Authorization: Bearer basura'.
    - Debe responder 401.
    """
    r = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "bearermalo@probando.com",
            "password": "Prueba123!",
            "nombre": "Bearer",
            "apellido": "Malo",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    assert r.status_code in (200, 201), r.text

    r = client_auth.post(
        "/api/v1/auth/login",
        json={"email": "bearermalo@probando.com", "password": "Prueba123!"},
    )
    assert r.status_code == 200, r.text

    r = client_auth.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer basura-total"},
    )
    assert r.status_code == 401, r.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_register_email_duplicado(client_auth: TestClient):
    r1 = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "dup@probando.com",
            "password": "Prueba123!",
            "nombre": "Dup",
            "apellido": "Uno",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    assert r1.status_code in (200, 201), r1.text

    r2 = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "dup@probando.com",
            "password": "OtraClave123!",
            "nombre": "Dup",
            "apellido": "Dos",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    assert r2.status_code in (400, 409), r2.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_register_email_invalido(client_auth: TestClient):
    r = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "no-es-un-email",
            "password": "Prueba123!",
            "nombre": "Mail",
            "apellido": "Invalido",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    assert r.status_code == 422, r.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_login_usuario_inexistente(client_auth: TestClient):
    r = client_auth.post(
        "/api/v1/auth/login",
        json={"email": "noexiste@probando.com", "password": "LoQueSea123!"},
    )
    assert r.status_code == 401, r.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_refresh_sin_campo_obligatorio(client_auth: TestClient):
    r = client_auth.post("/api/v1/auth/refresh", json={})
    assert r.status_code == 422, r.text


@pytest.mark.authflow
@pytest.mark.auth_neg
def test_me_con_token_expirado(client_auth: TestClient):
    r_reg = client_auth.post(
        "/api/v1/auth/register-json",
        json={
            "email": "expira@probando.com",
            "password": "Prueba123!",
            "nombre": "Expira",
            "apellido": "Token",
            "es_profesional": False,
            "es_solicitante": True,
        },
    )
    assert r_reg.status_code in (200, 201), r_reg.text
    reg = r_reg.json()

    expired_token = AuthService.crear_access_token(
        data={
            "sub": reg["usuario_id"],
            "email": reg["email"],
            "roles": ["solicitante"],
        },
        expires_delta=timedelta(seconds=-1),
    )

    r_me = client_auth.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert r_me.status_code == 401, r_me.text
