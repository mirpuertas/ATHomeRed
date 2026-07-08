
# Tests - ATHomeRed

## Índice

- [Resumen](#resumen)
- [Cómo ejecutar los tests](#cómo-ejecutar-los-tests)
- [Estructura del directorio de tests](#estructura-del-directorio-de-tests)
- [Markers](#markers)
- [Detalle de los tests](#detalle-de-los-tests)
- [Tests end-to-end omitidos](#tests-end-to-end-omitidos)
- [Configuración](#configuración)
- [Resultados de la suite de tests](#resultados-de-la-suite-de-tests)
- [Notas](#notas)
- [Referencias](#referencias)

---

## Resumen

La suite de tests de ATHomeRed cubre de manera exhaustiva la lógica de dominio, los endpoints de la API y la integración con bases de datos y servicios externos, en el contexto específico de acompañantes terapéuticos y enfermería domiciliaria. Actualmente, la gran mayoría de los tests están activos y pasan correctamente, incluyendo pruebas unitarias, de integración y de autenticación. Los tests end-to-end (E2E) que requieren infraestructura real están documentados y preparados, pero deshabilitados por defecto para evitar efectos colaterales en bases de datos reales. La cobertura es alta tanto en el dominio como en la API, y se mantiene actualizada conforme evoluciona el sistema.

---

## Cómo ejecutar los tests

Para ejecutar los tests (unitarios e integración), primero activa el entorno virtual de Python y luego ejecuta pytest desde la raíz del proyecto. Un flujo típico en Windows con PowerShell es:

```powershell
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar todos los tests (sin E2E)
pytest

# Ejecutar con más detalle
pytest -v

# Ejecutar solo tests de dominio
pytest tests/domain/ -v

# Ejecutar solo tests de API
pytest tests/api/ -v
````

Los tests que ejercitan integración real con base de datos usan una instancia de Supabase ya configurada para el proyecto, con esquema y datos seed cargados. Para estos casos, es necesario tener definidas las variables de entorno de conexión, según se detalla en `SUPABASE_TESTING.md`.

Los tests E2E están deshabilitados por defecto porque dependen de una base de datos real, variables de entorno configuradas y datos específicos ya cargados. Para ejecutarlos de manera explícita se puede utilizar:

```powershell
# Ejecutar solo tests E2E
pytest -m e2e

# Ejecutar toda la suite incluyendo E2E
pytest --runxfail
```

Es importante tener en cuenta que los tests E2E pueden modificar el estado de la base de datos.

---

## Estructura del directorio de tests

La estructura del directorio `tests/` refleja la separación de responsabilidades y facilita la ejecución selectiva y el mantenimiento. El árbol es:

```text
tests/
├── __init__.py                      # Inicializa el paquete de tests
├── conftest.py                      # Fixtures y configuración global para pytest
├── ESTADO_TESTS_COMPLETO.md         # Estado y cobertura de los tests
├── OBSERVERS_TESTS_README.md        # Documentación sobre tests de observers
├── README_TESTS.md                  # Instrucciones generales de testing
├── README.md                        # Documentación general de la carpeta tests
├── SUPABASE_TESTING.md              # Guía para tests con Supabase
├── test_integracion_api_domain.py   # Test de integración entre API y dominio
├── TESTING_GUIDE.md                 # Guía detallada de testing
├── __pycache__/                     # Caché de Python (archivos compilados)
├── api/                             # Tests de endpoints de la API y modelos mínimos
│   ├── __init__.py                  # Inicializa el subpaquete api
│   ├── auth_minimal_models.py       # Modelos mínimos para tests de autenticación
│   ├── test_auth.py                 # Tests de autenticación (login, registro, tokens, errores)
│   ├── test_busqueda.py             # Tests de endpoints de búsqueda (filtros, errores, resultados)
│   ├── test_pacientes.py            # Tests de endpoints de pacientes
│   └── __pycache__/                 # Caché de Python para api
├── domain/                          # Tests de lógica de dominio
│   ├── __init__.py                  # Inicializa el subpaquete domain
│   ├── test_buscador.py             # Tests de la clase Buscador y estrategias
│   ├── test_catalogo_integracion.py.disabled   # Test de integración de catálogo (deshabilitado)
│   ├── test_entities.py             # Tests de entidades del dominio (usuarios, pacientes, ubicaciones)
│   ├── test_estrategias_asignacion.py.disabled # Test de estrategias de asignación (deshabilitado)
│   ├── test_estrategias_busqueda.py # Tests de estrategias de búsqueda
│   ├── test_observers.py            # Tests de observers del dominio
│   └── test_regla_matriculas.py     # Tests de reglas de matrículas
└── integration/                     # Tests de integración con bases de datos y Supabase
    ├── __init__.py                  # Inicializa el subpaquete integration
    ├── README_SEED_TESTS.md         # Documentación sobre tests de seed
    ├── test_busqueda_con_bd.py      # Test de búsqueda con base de datos real (SQLite/Postgres)
    ├── test_busqueda_postgres.py    # Test de búsqueda usando Postgres
    ├── test_consistency_fix.py      # Test de consistencia y fixes
    ├── test_seed_validation.py      # Test de validación de datos seed
    └── test_supabase.py             # Test de integración con Supabase
```

Cada archivo y subcarpeta tiene un propósito claro: los tests de `api/` validan los endpoints y la lógica de negocio expuesta, los de `domain/` aseguran la robustez de las entidades y reglas del dominio, y los de `integration/` prueban la integración real con bases de datos y servicios externos. Los archivos de documentación y guías ayudan a entender la cobertura y el uso de la suite.

Esta organización separa claramente los tests del dominio, de la API, de autenticación y de la integración, facilitando la ejecución selectiva y el mantenimiento de la suite.

---

## Markers

Los tests se organizan mediante markers de pytest que permiten filtrar fácilmente qué subconjunto ejecutar. Existen markers para distinguir tests unitarios, de integración, del dominio, de la API y E2E. Algunos ejemplos de uso son:

```powershell
# Ejecutar únicamente tests unitarios
pytest -m unit

# Ejecutar únicamente tests de integración
pytest -m integration

# Ejecutar únicamente tests del domain layer
pytest -m domain

# Ejecutar únicamente tests del API layer
pytest -m api

# Ejecutar únicamente tests E2E (requieren base de datos real)
pytest -m e2e
```

En el caso particular de los tests de autenticación, también se utilizan markers específicos:

```powershell
# Todos los tests de autenticación definidos en test_auth.py
pytest -m authflow

# Solo casos positivos de autenticación
pytest -m auth_ok

# Solo casos negativos (errores esperados)
pytest -m auth_neg
```

Esta estrategia permite ajustar la granularidad de las ejecuciones según el objetivo (desarrollo rápido, integración, validación completa, smoke tests de auth, etcétera).

---

## Detalle de los tests

La suite cubre todos los niveles de la arquitectura.

En el dominio, los tests de entidades (`test_entities.py`) validan la creación, comparación y comportamiento de usuarios, profesionales, solicitantes, pacientes y ubicaciones, así como reglas de negocio como activación y desactivación, cálculo de edad y relaciones. Los tests de estrategias (`test_estrategias_busqueda.py`, `test_buscador.py`) ejercitan las búsquedas por zona, especialidad y combinadas, asegurando que la lógica de selección y filtrado funcione correctamente. Los tests de observers y reglas (`test_observers.py`, `test_regla_matriculas.py`) validan la correcta reacción ante eventos y la lógica de matrículas en el contexto de profesionales que brindan acompañamiento terapéutico y servicios de enfermería.

En la API, los tests de endpoints (`test_auth.py`, `test_busqueda.py`, `test_pacientes.py`) cubren el flujo completo de autenticación, la búsqueda de profesionales y la gestión de pacientes. El módulo `test_auth.py` implementa una batería de pruebas para el flujo mínimo de autenticación utilizando FastAPI y `TestClient` sobre una base SQLite en memoria. Se cubren casos de registro de usuario, login, obtención de `access_token` y `refresh_token`, acceso a endpoints protegidos mediante `Bearer` y renovación de tokens, además de casos negativos como contraseñas incorrectas, tokens inválidos o encabezados de autorización mal formados.

A nivel técnico, en estos tests de autenticación se sobreescribe la dependencia `get_db` para inyectar una sesión SQLite in-memory con `StaticPool`, se crean solo las tablas mínimas a partir de `Base.metadata.create_all` y se reemplazan los repositorios y el servicio de autenticación reales por versiones mínimas (fakes) pensadas para testing. Esto permite que las pruebas de auth sean rápidas y autocontenidas, sin depender de Postgres ni de migraciones, y se puedan ejecutar en cualquier entorno. Los markers `authflow`, `auth_ok` y `auth_neg` permiten ejecutar todo el flujo de autenticación o filtrar solo los casos positivos o negativos.

En la integración, los tests (`test_busqueda_con_bd.py`, `test_busqueda_postgres.py`, `test_seed_validation.py`, `test_supabase.py`, entre otros) validan la interacción real entre la API, los repositorios y la base de datos (SQLite o Postgres a través de Supabase), así como la integración con el proyecto remoto de Supabase preparado para ATHomeRed. La base de datos de integración no es genérica, sino que está diseñada específicamente para el dominio de acompañantes terapéuticos y enfermería domiciliaria.

El seed de datos crea una única provincia principal (Ciudad Autónoma de Buenos Aires), ocho comunas, veinticuatro barrios y distintas direcciones asociadas. Sobre esta geografía se definen solo seis especialidades, todas vinculadas al dominio del proyecto: Acompañamiento Terapéutico General, Acompañamiento Terapéutico en Geriatría, Acompañamiento Terapéutico con especialización en TEA/TDAH, Enfermería, Enfermería Geriátrica y Cuidados Paliativos. A partir de estas especialidades se generan cien profesionales y cincuenta pacientes de prueba. Cada profesional está asociado a una de estas especialidades, tiene matrícula válida (CABA o Provincia de Buenos Aires), biografía y años de experiencia, mientras que los pacientes se generan con edades y relaciones familiares coherentes con la especialidad que los atiende (por ejemplo, niños y adolescentes para TEA/TDAH, personas mayores para geriatría y cuidados paliativos). De esta forma, los tests de integración y búsqueda ejercitan escenarios realistas dentro del alcance concreto del proyecto, que se limita a acompañantes terapéuticos y enfermeros.

La mayoría de los tests están activos y pasan correctamente. Solo algunos archivos con sufijo `.disabled` corresponden a pruebas que requieren infraestructura especial o que están en desarrollo.

---

## Tests end-to-end omitidos

Los tests end-to-end (E2E) están preparados para validar flujos completos de usuario a través de la API, como la gestión integral de pacientes (creación, obtención, listado, actualización y eliminación) o búsquedas complejas combinando filtros. Estos tests requieren una base de datos real y datos pre-cargados, por lo que están deshabilitados por defecto para evitar efectos colaterales.

En el contexto de ATHomeRed, los E2E están pensados para ejecutarse contra la base de datos real del proyecto (por ejemplo, la instancia de Supabase con el seed completo de profesionales y pacientes). Se recomienda habilitarlos solo en entornos de pruebas aislados, quitando la extensión `.disabled` de los archivos correspondientes o ejecutándolos con markers específicos si el entorno está correctamente configurado.

---

## Configuración

La configuración principal de pytest se encuentra en el archivo `pytest.ini`, donde se definen los patrones de descubrimiento de tests y los markers disponibles:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*

markers =
    e2e: Tests End-to-End (requieren DB real)
    unit: Tests unitarios
    integration: Tests de integración
    domain: Tests del domain layer
    api: Tests de API layer
    authflow: Flujo completo de autenticación mínima
    auth_ok: Casos positivos de autenticación
    auth_neg: Casos negativos de autenticación
```

El archivo `conftest.py` centraliza las fixtures compartidas que facilitan la creación de datos de prueba consistentes. Allí se definen ubicaciones y direcciones de ejemplo, especialidades del dominio (acompañamiento terapéutico general, geriatría, TEA/TDAH, enfermería, enfermería geriátrica y cuidados paliativos), disponibilidades, matrículas asociadas a distintas jurisdicciones, profesionales con sus especialidades y disponibilidades, solicitantes y pacientes, filtros de búsqueda y mocks de repositorios. Esto permite que los tests se enfoquen en la lógica y no en el armado repetitivo de datos.

---

## Resultados de la suite de tests

Una ejecución típica de la suite completa (sin E2E) muestra que la mayoría de los tests pasan exitosamente. Los pocos warnings suelen estar relacionados con deprecaciones de Pydantic y no afectan la validez de los tests ni de la aplicación. La cobertura es alta y se mantiene actualizada a medida que el sistema evoluciona.

---

## Notas

Se recomienda mantener los tests E2E deshabilitados salvo que se cuente con un entorno de base de datos aislado para pruebas, ya que pueden modificar datos reales. Los tests unitarios e integración son rápidos, reproducibles y, salvo los casos que ejercitan explícitamente Supabase, no dependen de infraestructura externa, por lo que deben ser la base de la validación continua.

El hecho de contar con un seed completo en la base de datos (a través del ORM) que crea cien profesionales y cincuenta pacientes coherentes con las especialidades y edades esperadas, permite que los tests de integración y búsqueda se ejecuten sobre escenarios realistas del caso de uso de ATHomeRed, sin necesidad de preparar datos manualmente en cada ejecución.

---

## Referencias

Para el enfoque adoptado en la escritura y organización de las pruebas se tomaron como referencia la documentación oficial de pytest, que describe buenas prácticas para estructurar suites de tests y utilizar markers; la documentación de FastAPI sobre testing, que muestra cómo ejercitar la API utilizando `TestClient`; los principios de desarrollo guiado por tests (TDD), que proponen el ciclo Red–Green–Refactor; y las ideas de arquitectura limpia, que fomentan testear la lógica de dominio sin dependencias duras de infraestructura externa.

---

Proyecto: ATHomeRed – Plataforma de Acompañantes Terapéuticos y Enfermería
Proyecto: ATHomeRed – Plataforma de Acompañantes Terapéuticos y Enfermería
