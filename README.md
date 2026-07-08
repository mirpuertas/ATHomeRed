# 🩺 ATHomeRed – API para atención domiciliaria

ATHomeRed es una API REST desarrollada con **FastAPI** para modelar una red de atención domiciliaria que busca conectar familias (representadas por un **Responsable/Solicitante**) y profesionales del área de la salud domiciliaria, como **acompañantes terapéuticos** y **enfermeros/as**.

El sistema permite registrar usuarios, diferenciar roles, gestionar pacientes, buscar profesionales por criterios específicos y administrar consultas/reservas con estados de negocio.

Proyecto académico grupal de **Programación II (2.º Cuatrimestre 2025, UNSAM)**.

## Problema que aborda

En Argentina, la enfermería domiciliaria y el acompañamiento terapéutico suelen presentar problemas de informalidad, baja trazabilidad y dificultad para encontrar profesionales validados.

Algunos de los problemas detectados son:

- búsqueda de profesionales basada en recomendaciones informales;
- dificultad para validar matrículas o credenciales;
- falta de trazabilidad sobre reservas, consultas y estados de atención;
- desigualdad geográfica en la disponibilidad de profesionales;
- escasa formalización de los vínculos entre familias y prestadores.

ATHomeRed plantea una red digital para organizar ese proceso, conectando solicitantes y pacientes con profesionales de salud domiciliaria mediante una API extensible.

## Objetivo

Construir una API orientada a objetos para organizar el vínculo entre solicitantes, pacientes y profesionales de atención domiciliaria, incorporando:

- registro y autenticación de usuarios;
- roles diferenciados para profesionales y solicitantes;
- gestión de pacientes asociados a responsables;
- búsqueda de profesionales por zona, especialidad o criterios combinados;
- administración de consultas/reservas con estados de negocio;
- persistencia relacional con PostgreSQL;
- arquitectura modular por capas;
- patrones de diseño aplicados al dominio.

## Funcionalidades principales

- Registro de usuarios.
- Roles diferenciados para profesionales y solicitantes.
- Autenticación mediante JWT.
- Hash de contraseñas con Argon2.
- Gestión de pacientes asociados a solicitantes.
- Gestión de profesionales y especialidades.
- Búsqueda de profesionales por zona, especialidad o criterios combinados.
- Creación y administración de consultas/reservas.
- Estados de consulta: pendiente, confirmada, completada, cancelada y reprogramada.
- Validaciones de negocio antes de crear o modificar consultas.
- Gestión de valoraciones.
- Eventos de dominio asociados a cambios de estado.
- Notificaciones simuladas mediante Observer/EventBus.
- Persistencia relacional con SQLAlchemy.
- Migraciones versionadas con Alembic.
- Tests con Pytest.

## Stack técnico

- **Lenguaje**: Python 3.11+
- **API**: FastAPI
- **Servidor ASGI**: Uvicorn
- **Validación**: Pydantic
- **ORM**: SQLAlchemy
- **Base de datos**: PostgreSQL / Supabase
- **Migraciones**: Alembic
- **Autenticación**: JWT con HS256
- **Seguridad**: Argon2 para hash de contraseñas
- **Configuración**: variables de entorno con `.env`
- **Testing**: Pytest
- **Contenedores**: Docker / Docker Compose
- **CI**: GitHub Actions para linting y formato
- **Documentación API**: OpenAPI / Swagger UI generada por FastAPI

## Arquitectura general

El proyecto sigue una arquitectura por capas, separando responsabilidades entre API, dominio, infraestructura y servicios de aplicación. 

```
app/
├── api/          # Routers, schemas, dependencias y policies
├── domain/       # Entidades, value objects, eventos, estrategias y observers
├── infra/        # Persistencia, modelos ORM y repositorios
├── services/     # Servicios de aplicación, como autenticación
└── static/       # UI mínima de demo
```
La idea principal de esta separación es mantener el dominio desacoplado de FastAPI, SQLAlchemy y otros detalles de infraestructura.

Para una descripción técnica más detallada del diseño, las capas, los patrones y la persistencia, ver:

- [Documentación técnica](docs/ARCHITECTURE.md)

## Patrones aplicados

El proyecto aplica principalmente los patrones **Strategy**, **Observer** y **Repository**.

- **Strategy**: utilizado en el módulo de búsqueda de profesionales, permitiendo cambiar el criterio de búsqueda sin modificar los endpoints principales.
- **Observer / EventBus**: utilizado para reaccionar a eventos de dominio, como cambios de estado en una consulta.
- **Repository**: utilizado para separar la lógica de dominio de los detalles de persistencia con SQLAlchemy.

## Mi aporte principal

Dentro del trabajo grupal, mi participación se concentró principalmente en la infraestructura técnica del proyecto, la persistencia y el mantenimiento del repositorio.

Mis aportes principales incluyeron:

- organización y mantenimiento del repositorio en GitHub;
- configuración inicial del flujo de trabajo con ramas, commits y estructura del proyecto;
- diseño e implementación del modelo de persistencia;
- definición de modelos ORM con SQLAlchemy;
- configuración y uso de Supabase como base PostgreSQL;
- configuración de Alembic para versionado y migraciones de base de datos;
- armado de scripts auxiliares para creación, limpieza, seed y verificación de la base;
- integración entre la capa de dominio, repositorios y modelos de persistencia;
- configuración básica de CI con GitHub Actions para controles de estilo/linting;
- colaboración en la organización general de la arquitectura por capas.

También participé en decisiones de diseño vinculadas al modelo de dominio, la separación entre usuarios, profesionales, solicitantes y pacientes, y la integración de los patrones trabajados en la materia.

## Diagrama UML

El proyecto incluye un diagrama UML de dominio:

- [Diagrama de clases de dominio](docs/uml/UML_ATHomeRed_Domain.svg)

El diagrama resume las entidades principales, value objects, relaciones y patrones aplicados dentro del modelo de dominio.

## API rápida

La API expone endpoints agrupados por recurso bajo el prefijo `/api/v1`.

### Autenticación
- `POST /api/v1/auth/register-json`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Ejemplo de login:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"probando@gmail.com","password":"Prueba123."}'
```

La respuesta devuelve un token de acceso:

```json
{
  "access_token": "token_jwt",
  "token_type": "bearer"
}
```

Luego puede utilizarse en endpoints protegidos mediante el header:
```text
Authorization: Bearer <token>
```

## Ejecución local

Crear y activar entorno virtual:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
```

Instalar dependencias:
```bash
pip install -r requirements.txt
```

Crear archivo de variables de entorno:
```bash
cp .env.example .env
```

Configurar variables necesarias en `.env`:
```env
DATABASE_URL=
AT_HOME_RED_SECRET=
ACCESS_TOKEN_EXPIRE_MINUTES=
```
Levantar la API:
```bash
uvicorn app.main:app --reload
```
La API queda disponible en:
```text
http://localhost:8000
```
La documentación Swagger se genera automáticamente en:
```text
http://localhost:8000/docs
```

## Docker y base de datos
```bash
docker compose -f docker/docker-compose.yml up -d   # levanta PostgreSQL
alembic upgrade head                                 # aplica migraciones
uvicorn app.main:app --reload                        # levanta la API
```

## Migraciones
```bash
# Crear una nueva migración
alembic revision -m "descripcion" --autogenerate

# Aplicar migraciones:
alembic upgrade head

# Revertir la última migración:
alembic downgrade -1
```

## Tests

Ejecutar todos los tests:
```bash
pytest
```
Ejecutar subconjuntos específicos:

```bash
pytest tests/api
pytest tests/domain
pytest tests/integration
```

## Estado del proyecto

El MVP implementa los flujos principales de autenticación, usuarios, profesionales, pacientes, búsqueda, consultas/reservas y valoraciones.

El despliegue original utilizado para la entrega no se mantiene activo actualmente. El proyecto está preparado para ejecutarse localmente y generar documentación Swagger en `/docs`.

## Autoría y créditos

Proyecto desarrollado en equipo por:

- Federico Nicolás Llanes – [@FedeLlanes](https://github.com/FedeLlanes)
- Miguel Ignacio Rodríguez Puertas – [@mirpuertas](https://github.com/mirpuertas)
- Ayelén Luján Scafati – [@ayescafati](https://github.com/ayescafati)

Esta versión se mantiene en mi repositorio personal como parte de mi portfolio técnico. Mi aporte principal se detalla en la sección correspondiente.

## Licencia

Este proyecto está bajo la licencia MIT. [Ver LICENSE](./LICENSE).
