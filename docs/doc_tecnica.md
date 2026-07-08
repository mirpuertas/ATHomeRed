# ATHomeRed – Notas técnicas y arquitectura

Este documento complementa el `README.md` principal con detalles internos de arquitectura, persistencia, dominio y patrones aplicados.

No busca repetir la presentación general del proyecto, sino documentar cómo está organizado internamente el sistema.

## Estructura extendida del repositorio

```text
ATHomeRed/
├── app/
│   ├── main.py                       # Punto de entrada de FastAPI
│   ├── api/                          # Capa HTTP: routers, schemas, dependencies y policies
│   │   ├── dependencies.py           # Dependencias comunes
│   │   ├── event_bus.py              # Wiring del EventBus y observers
│   │   ├── exceptions.py             # Excepciones y handlers HTTP
│   │   ├── policies.py               # Policies de validación/autorización
│   │   ├── schemas.py                # DTOs / modelos Pydantic
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── busqueda.py
│   │       ├── consultas.py
│   │       ├── pacientes.py
│   │       ├── profesionales.py
│   │       └── valoraciones.py
│   ├── domain/                       # Modelo de dominio
│   │   ├── entities/
│   │   │   ├── agenda.py
│   │   │   ├── catalogo.py
│   │   │   ├── usuarios.py
│   │   │   └── valoraciones.py
│   │   ├── enumeraciones.py
│   │   ├── eventos.py
│   │   ├── observers/
│   │   ├── strategies/
│   │   └── value_objects/
│   ├── infra/                        # Infraestructura: ORM, repositorios y DB
│   │   ├── persistence/
│   │   └── repositories/
│   ├── services/
│   │   └── auth_service.py
│   └── static/                       # UI mínima embebida para demo
├── alembic/                          # Migraciones
├── docker/                           # Dockerfile y docker-compose
├── scripts/                          # Scripts auxiliares de base de datos
├── tests/                            # Tests unitarios e integración
└── .github/workflows/                # CI básica
```

## Implementación por módulos

### API y routers

La aplicación se instancia en `app/main.py` y publica endpoints agrupados por dominio bajo `app/api/routers/`.

Los routers principales son:

- `auth.py`: registro, login y perfil autenticado
- `busqueda.py`: búsqueda de profesionales
- `consultas.py`: gestión de consultas/reservas
- `pacientes.py`: gestión de pacientes
- `profesionales.py`: gestión de profesionales
- `valoraciones.py`: gestión de valoraciones

Esta organización mantiene separado el contrato HTTP de la lógica de dominio y facilita la navegación desde la documentación Swagger generada automáticamente en `/docs`.

## Autenticación y seguridad

El flujo de autenticación usa **Argon2** para hash de contraseñas y **JWT HS256** para tokens de acceso.

El router `app/api/routers/auth.py`, bajo el prefijo `/api/v1/auth`, expone:

- `POST /register-json`: alta de usuario
- `POST /login`: autenticación y generación de token
- `GET /me`: perfil básico del usuario autenticado

La lógica principal vive en `app/services/auth_service.py`.

Responsabilidades de `AuthService`:

- `hash_password`
- `verify_password`
- `crear_access_token`
- `validar_access_token`
- manejo de expiración mediante `ACCESS_TOKEN_EXPIRE_MINUTES`
- uso de `AT_HOME_RED_SECRET` como clave de firma

El repositorio de usuarios participa en operaciones como:

- búsqueda por email
- incremento de intentos fallidos
- verificación de bloqueo temporal
- reseteo de intentos fallidos
- actualización del último login

## Persistencia y migraciones

El modelo de datos está implementado con **SQLAlchemy** y versionado con **Alembic**.

La capa de persistencia se encuentra en:

```text
app/infra/persistence/
```

La capa de repositorios se encuentra en:
```text
app/infra/repositories/
```

La separación entre modelos ORM y repositorios permite que el dominio no dependa directamente de SQLAlchemy ni del esquema físico de la base de datos.

Durante el desarrollo académico se utilizó **Supabase** como proveedor de PostgreSQL en la nube. La aplicación puede conectarse a otra instancia PostgreSQL compatible configurando `DATABASE_URL`.

### Alembic

Alembic se utiliza para crear, aplicar y revertir migraciones del esquema.

Archivos relevantes:

```text
alembic.ini
alembic/
├── env.py
├── script.py.mako
└── versions/
```

Comandos principales:

```bash
alembic revision -m "descripcion" --autogenerate
alembic upgrade head
alembic downgrade -1
```

## Scripts auxiliares de base de datos

El proyecto incluye scripts para preparar, limpiar y verificar la base de datos.

```text
scripts/
├── database/
│   ├── apply_sql.py
│   ├── create_schema.py
│   ├── ejecutar_seed.py
│   ├── limpiar_bd.py
│   └── seed_completo_uuid.sql
└── utils/
    ├── check_db.py
    ├── test_connection.py
    └── verify_seed.py
```

Estos scripts fueron usados para iterar sobre el modelo de persistencia, cargar datos iniciales, validar conexiones y verificar consistencia del entorno.

## Consultas y reservas

El módulo de consultas permite:

- crear consultas
- leer consultas
- actualizar consultas
- cancelar consultas
- confirmar consultas
- completar consultas
- reprogramar consultas
- listar consultas por profesional
- listar consultas por paciente

Antes de persistir una consulta se aplican validaciones de integridad y reglas de negocio:

- profesional verificado
- profesional activo
- solicitante activo
- vínculo válido entre paciente y solicitante
- horarios consistentes
- fechas no pasadas
- ausencia de solapamientos

Cada cambio relevante de estado puede disparar un evento de dominio publicado en el `EventBus`.

## Búsqueda de profesionales

El módulo de búsqueda usa el patrón **Strategy**.

El router construye un `FiltroBusqueda` a partir del DTO recibido, resuelve la especialidad por nombre o ID usando el catálogo y valida los criterios de entrada.

Según los criterios ingresados, selecciona una estrategia de dominio y ejecuta el contexto `Buscador`.

Estrategias principales:

| Estrategia | Criterio |
|---|---|
| `BusquedaPorZona` | Búsqueda por ubicación o zona. |
| `BusquedaPorEspecialidad` | Búsqueda por especialidad. |
| `BusquedaCombinada` | Búsqueda por zona y especialidad. |

Este diseño permite cambiar o extender la lógica de búsqueda sin modificar los endpoints principales.

## Eventos de dominio y notificaciones

El sistema emite eventos de dominio ante cambios relevantes en las consultas/reservas.

Eventos principales:

- `CitaCreada`
- `CitaConfirmada`
- `CitaCancelada`
- `CitaCompletada`
- `CitaReprogramada`

Los eventos se procesan mediante un `EventBus` simple.

El bus permite suscribir:

- handlers funcionales
- observers tradicionales

Observers incluidos:

| Observer | Rol |
|---|---|
| `NotificadorEmail` | Simula envío de notificaciones por consola. |
| `AuditLogger` | Registra eventos relevantes en logs. |

En el MVP, las notificaciones funcionan en modo demostrativo. La estructura permite reemplazarlas por integraciones reales, como SMTP, sin modificar las entidades que emiten eventos.

## Modelo de usuarios

El dominio separa explícitamente quién tiene cuenta de acceso y quién recibe la atención.

### Usuario

Clase base abstracta para los roles operativos del sistema.

Atributos principales:

- `id`
- `nombre`
- `apellido`
- `email`
- `celular`
- `ubicacion`
- `activo`

Métodos principales:

- `nombre_completo`
- `activar`
- `desactivar`
- `datos_contacto`

### Profesional

Hereda de `Usuario` y representa a un profesional de salud domiciliaria.

Puede tener:

- especialidades
- disponibilidades
- matrículas
- consultas asociadas
- valoraciones

Métodos principales:

- `agregar_disponibilidad`
- `agregar_matricula`

### Solicitante

Hereda de `Usuario` y representa a quien gestiona una consulta propia o de una persona a cargo.

Mantiene relación con un paciente y puede administrar consultas/reservas.

Método principal:

- `agregar_paciente`

### Paciente

Representa a la persona atendida.

No hereda de `Usuario`, porque puede no tener cuenta propia dentro del sistema.

Atributos principales:

- `id`
- `nombre`
- `apellido`
- `fecha_nacimiento`
- `ubicacion`
- `solicitante_id`
- `relacion`
- `notas`

Métodos principales:

- `edad`
- `nombre_completo`
- `es_menor`

### Nota de diseño

Se separa explícitamente “quién tiene cuenta” (`Usuario`) de “quién recibe la atención” (`Paciente`).

Esto permite modelar casos donde un responsable o solicitante gestiona la atención de otra persona.

## Clases principales

### Entidades y value objects

| Clase / estructura | Rol | Ubicación |
|---|---|---|
| `Usuario` | Base abstracta de usuarios con cuenta. | `app/domain/entities/usuarios.py` |
| `Profesional` | Profesional que ofrece servicios de salud domiciliaria. | `app/domain/entities/usuarios.py` |
| `Solicitante` | Responsable que gestiona consultas propias o de un paciente. | `app/domain/entities/usuarios.py` |
| `Paciente` | Persona atendida, sin necesidad de cuenta propia. | `app/domain/entities/usuarios.py` |
| `Cita` | Consulta/reserva con estados y métodos de negocio. | `app/domain/entities/agenda.py` |
| `Ubicacion` | Value object de localización. | `app/domain/value_objects/objetos_valor.py` |
| `Disponibilidad` | Value object de días y horarios de atención. | `app/domain/value_objects/objetos_valor.py` |
| `Matricula` | Datos de matrícula profesional. | `app/domain/entities/usuarios.py` |
| `Especialidad` | Tipo de servicio profesional. | `app/domain/entities/catalogo.py` |
| `Tarifa` | Precio o vigencia asociada a una especialidad. | `app/domain/entities/catalogo.py` |
| `Publicacion` | Información pública del profesional. | `app/domain/entities/catalogo.py` |
| `FiltroBusqueda` | Criterios de búsqueda de profesionales. | `app/domain/entities/catalogo.py` |

### Autenticación

| Componente / DTO | Rol | Ubicación |
|---|---|---|
| `AuthService` | Hash Argon2, JWT HS256, registro/login y bloqueo por intentos. | `app/services/auth_service.py` |
| `UsuarioRepository` | Acceso a usuarios, intentos fallidos y último login. | `app/infra/repositories/usuario_repository.py` |
| `RegisterRequest` | DTO de registro. | `app/api/schemas.py` |
| `LoginRequest` | DTO de login. | `app/api/schemas.py` |
| `TokenSchema` | Respuesta `{access_token, token_type}`. | `app/api/schemas.py` |
| `auth.py` | Router de autenticación. | `app/api/routers/auth.py` |

### Búsqueda y Strategy

| Clase / interfaz | Rol | Ubicación |
|---|---|---|
| `Buscador` | Contexto que aplica la estrategia activa. | `app/domain/strategies/buscador.py` |
| `Estrategia` | Contrato base de estrategias. | `app/domain/strategies/estrategia.py` |
| `BusquedaPorZona` | Estrategia por ubicación. | `app/domain/strategies/estrategia.py` |
| `BusquedaPorEspecialidad` | Estrategia por especialidad. | `app/domain/strategies/estrategia.py` |
| `BusquedaCombinada` | Estrategia combinada. | `app/domain/strategies/estrategia.py` |
| `EstrategiaAsignacion` | Políticas de asignación o validación. | `app/domain/strategies/estrategia_asignacion.py` |

### Notificaciones y Observer

| Clase / servicio | Rol | Ubicación |
|---|---|---|
| `Observer` / `Subject` | Base del patrón Observer. | `app/domain/observers/observadores.py` |
| `EventBus` | Publicación y suscripción de eventos. | `app/api/event_bus.py` |
| `NotificadorEmail` | Observer demo de notificación por consola. | `app/domain/observers/observadores.py` |
| `AuditLogger` | Observer de auditoría por logs. | `app/domain/observers/observadores.py` |
| Eventos de `Cita` | Eventos del flujo de consultas/reservas. | `app/domain/eventos.py` |

### Enumeraciones

| Enum | Uso | Ubicación |
|---|---|---|
| `EstadoCita` | Estados del flujo de consulta/reserva. | `app/domain/enumeraciones.py` |
| `DiaSemana` | Días disponibles para horarios de atención. | `app/domain/enumeraciones.py` |

## Patrones aplicados en el diseño

| Patrón | Uso en el proyecto |
|---|---|
| `Strategy` | Selección dinámica de criterios de búsqueda de profesionales. |
| `Observer / EventBus` | Publicación y reacción ante eventos de dominio, especialmente cambios de estado en consultas/reservas. |
| `Repository` | Separación entre dominio y persistencia con SQLAlchemy. |

## Uso de decoradores

El proyecto usa decoradores de Python, FastAPI y Pytest de forma transversal.

Ejemplos:

- rutas de FastAPI con `@app.get(...)` y `@router.post(...)`
- inyección de dependencias con `Depends(...)`
- utilidades con `@staticmethod`
- marcas de Pytest como `@pytest.mark`

Estos decoradores se usan de manera idiomática dentro del lenguaje y del framework.

No se modela un patrón GoF `Decorator` como objeto de dominio.
