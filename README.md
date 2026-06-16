# activia-trace

Plataforma de gestión académica y trazabilidad multi-tenant. Opera como capa de orquestación sobre Moodle: consolida calificaciones, detecta alumnos atrasados, gestiona comunicación saliente con aprobación docente, equipos, encuentros, coloquios, liquidaciones de honorarios y auditoría completa.

Cada institución es un **tenant aislado**. Todo audita.

---

## Tabla de contenidos

- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Requisitos previos](#requisitos-previos)
- [Configuración del entorno](#configuración-del-entorno)
- [Ejecución con Docker (recomendado)](#ejecución-con-docker-recomendado)
- [Ejecución en desarrollo local](#ejecución-en-desarrollo-local)
- [Migraciones de base de datos](#migraciones-de-base-de-datos)
- [Testing](#testing)
- [Estructura del proyecto](#estructura-del-proyecto)
- [API Reference](#api-reference)
- [Roles y permisos](#roles-y-permisos)
- [Variables de entorno](#variables-de-entorno)
- [Deploy en producción (Easypanel)](#deploy-en-producción-easypanel)

---

## Stack tecnológico

### Backend

| Componente | Tecnología | Versión |
|---|---|---|
| Lenguaje | Python | 3.13 |
| Framework | FastAPI | ≥0.115 |
| ORM | SQLAlchemy (async) | 2.0 |
| Migraciones | Alembic | ≥1.13 |
| Base de datos | PostgreSQL | 16 |
| Validación | Pydantic v2 | ≥2.9 |
| Auth | JWT (HS256) + Argon2id + TOTP | — |
| Cifrado en reposo | AES-256-GCM | — |
| Background jobs | Worker async propio | — |
| Integración LMS | Moodle Web Services (httpx) | — |
| Observabilidad | OpenTelemetry + logs JSON | — |
| Servidor ASGI | Uvicorn | ≥0.30 |
| Packaging | uv (fast installer) | 0.4.30 |

### Frontend

| Componente | Tecnología | Versión |
|---|---|---|
| Framework | React + TypeScript | 18 / 5.x |
| Bundler | Vite | ≥5.4 |
| Server state | TanStack Query | v5 |
| Formularios | React Hook Form + Zod | v7 / v3 |
| Estilos | Tailwind CSS | ≥3.4 |
| HTTP client | Axios | ≥1.7 |
| Testing | Vitest + Testing Library | ≥4.1 |
| Router | React Router DOM | v6 |

### Infraestructura

| Componente | Tecnología |
|---|---|
| Contenedores | Docker + Docker Compose |
| Deploy | Easypanel |
| CI/CD | GitHub (ramas por change) |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (SPA)                       │
│  React 18 · TanStack Query · RHF+Zod · Tailwind · Axios     │
│  features: auth · comision · coordinacion · finanzas · admin │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP / REST
┌─────────────────────▼───────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│                                                             │
│  Routers → Services → Repositories → Models (SQLAlchemy)    │
│                                                             │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────┐   │
│  │  Auth + JWT │   │ RBAC fino    │   │  Audit Log     │   │
│  │  Argon2id   │   │ modulo:accion│   │  append-only   │   │
│  │  2FA TOTP   │   │ fail-closed  │   │  inmutable     │   │
│  └─────────────┘   └──────────────┘   └────────────────┘   │
│                                                             │
│  Multi-tenancy row-level (tenant_id en cada tabla)          │
│  AES-256-GCM para PII sensible (CUIL, CBU, DNI)             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼──────────┐   ┌────────────────────────┐
│        PostgreSQL 16           │   │    Worker async         │
│  17 migraciones Alembic        │   │  Cola de comunicaciones │
│  Soft delete · UUID PKs        │   │  Pend→Send→OK/Fail      │
└────────────────────────────────┘   └────────────────────────┘
```

El patrón de capas es **unidireccional y estricto**:
- **Routers**: reciben requests, validan con Pydantic, llaman a Services. Sin lógica de negocio.
- **Services**: lógica de dominio, orquestación. Sin acceso directo a DB.
- **Repositories**: única capa que toca SQLAlchemy. Siempre filtran por `tenant_id`.
- **Models**: definición ORM. Soft delete en todas las entidades.

---

## Requisitos previos

- [Docker](https://www.docker.com/) ≥ 24 y Docker Compose ≥ 2.20
- [Node.js](https://nodejs.org/) ≥ 20 (solo para desarrollo frontend local)
- [Python](https://www.python.org/) ≥ 3.13 (solo para desarrollo backend local)
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes Python, opcional para local)

---

## Configuración del entorno

### 1. Clonar el repositorio

```bash
git clone https://github.com/JereBon/active-trace-BontornoVernierMas.git
cd active-trace-BontornoVernierMas
```

### 2. Crear el archivo de entorno del backend

```bash
cp backend/.env.example backend/.env
```

Editar `backend/.env` con los valores reales (ver [Variables de entorno](#variables-de-entorno)).

Los valores mínimos para desarrollo local:

```env
DATABASE_URL=postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace
DATABASE_URL_TEST=postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test
SECRET_KEY=una-clave-secreta-de-al-menos-32-caracteres-aqui
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

> **`ENCRYPTION_KEY`** debe ser exactamente 64 caracteres hexadecimales (= 32 bytes para AES-256-GCM).
> Generá una clave segura con: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## Ejecución con Docker (recomendado)

Levanta los tres servicios (PostgreSQL, API, Worker) en un solo comando:

```bash
docker-compose up --build
```

Servicios disponibles:

| Servicio | URL |
|---|---|
| API REST | http://localhost:8000 |
| Docs interactivos (Swagger) | http://localhost:8000/docs |
| Docs alternativos (ReDoc) | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |

### Comandos útiles

```bash
# Levantar en background
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f api
docker-compose logs -f worker

# Bajar y eliminar volúmenes (reset completo de DB)
docker-compose down -v

# Ejecutar migraciones manualmente dentro del contenedor
docker-compose exec api alembic upgrade head

# Acceder a la DB con psql
docker-compose exec postgres psql -U activia -d activia_trace
```

### Aplicar migraciones (primera vez)

Las migraciones se aplican automáticamente al iniciar el contenedor `api`. Si necesitás correrlas manualmente:

```bash
docker-compose exec api alembic upgrade head
```

---

## Ejecución en desarrollo local

### Backend

```bash
cd backend

# Instalar dependencias (con uv)
uv venv
uv pip install -e ".[dev]"

# O con pip clásico
pip install -e ".[dev]"

# Aplicar migraciones (requiere PostgreSQL corriendo)
alembic upgrade head

# Levantar el servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```

El servidor se recarga automáticamente con cada cambio en el código.

### Worker (en otra terminal)

```bash
cd backend
python -m app.workers.main
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Levantar servidor de desarrollo con HMR
npm run dev
```

Disponible en: **http://localhost:5173**

> El frontend apunta al backend en `http://localhost:8000` por defecto. Ajustar en `frontend/src/shared/services/api.ts` si el puerto difiere.

---

## Migraciones de base de datos

El proyecto usa **Alembic** con una migración por cada cambio de schema.

```bash
# Ver el estado actual
alembic current

# Ver el historial completo
alembic history --verbose

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Revertir la última migración
alembic downgrade -1

# Revertir todo
alembic downgrade base
```

### Historial de migraciones

| # | Nombre | Contenido |
|---|---|---|
| 0001 | `tenant` | Modelo Tenant raíz |
| 0002 | `usuario_auth` | Usuarios, refresh tokens, 2FA |
| 0003 | `rbac` | Roles, permisos, seed de la matriz completa |
| 0004 | `audit_log` | Log de auditoría append-only |
| 0005 | `estructura_academica` | Carrera, Cohorte, Materia |
| 0006 | `avisos_y_acks` | Aviso, AcknowledgmentAviso |
| 0007 | `programas_y_fechas_academicas` | ProgramaMateria, FechaAcademica |
| 0008 | `usuarios_pii_asignaciones` | PII cifrada, Asignacion |
| 0009 | `version_padron_entrada_padron` | Padrón de alumnos, import |
| 0010 | `calificacion_umbral_materia` | Calificacion, UmbralMateria |
| 0011 | `encuentros_y_guardias` | SlotEncuentro, InstanciaEncuentro, Guardia |
| 0012 | `add_finalizado_lms_calificacion` | Campos extra en Calificacion |
| 0013 | `comunicacion` | Comunicacion, cola de mensajes |
| 0014 | `tareas_y_comentarios` | Tarea, ComentarioTarea |
| 0015 | `evaluaciones_y_coloquios` | Evaluacion, ReservaEvaluacion, ResultadoEvaluacion |
| 0016 | `mensaje_interno` | MensajeInterno (mensajería interna entre usuarios) |
| 0017 | `liquidaciones_y_honorarios` | SalarioBase, SalarioPlus, Liquidacion, Factura + `categoria_clave` en Materia |

---

## Testing

### Backend

```bash
cd backend

# Correr todos los tests
pytest

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing

# Tests de un módulo específico
pytest tests/test_auth.py -v
pytest tests/test_liquidaciones.py -v

# En paralelo (más rápido)
pytest -n auto
```

> Los tests usan **PostgreSQL real** (no mocks de DB). Se requiere que la variable `DATABASE_URL_TEST` apunte a una base de test separada.

Cobertura mínima objetivo: **≥80% de líneas**, **≥90% de reglas de negocio**.

### Frontend

```bash
cd frontend

# Correr todos los tests (modo CI)
npm test

# Modo watch (desarrollo)
npm run test:watch

# Con cobertura
npm run test -- --coverage
```

---

## Estructura del proyecto

```
active-trace/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routers/          # Endpoints REST (un archivo por dominio)
│   │   ├── core/
│   │   │   ├── config.py             # Settings (Pydantic v2)
│   │   │   ├── database.py           # Engine async + session factory
│   │   │   ├── security.py           # JWT, Argon2id, AES-256
│   │   │   ├── permissions.py        # Guards RBAC (require_permission)
│   │   │   └── audit.py              # Helper audit_action()
│   │   ├── models/                   # ORM SQLAlchemy (una entidad por archivo)
│   │   ├── repositories/             # Acceso a DB (único punto de contacto)
│   │   ├── schemas/                  # DTOs Pydantic (request/response)
│   │   ├── services/                 # Lógica de negocio
│   │   ├── integrations/
│   │   │   └── moodle_ws.py          # Cliente Moodle Web Services
│   │   └── workers/
│   │       └── main.py               # Worker de cola de comunicaciones
│   ├── alembic/
│   │   └── versions/                 # 17 migraciones Alembic
│   ├── tests/                        # Tests de integración (pytest + PostgreSQL real)
│   ├── Dockerfile                    # Multi-stage (builder + runtime)
│   └── pyproject.toml
│
├── frontend/
│   └── src/
│       ├── features/
│       │   ├── auth/                 # Login, guard de rutas, refresh transparente
│       │   ├── comision/             # PROFESOR: importación, atrasados, comunicaciones
│       │   ├── coordinacion/         # COORDINADOR: equipos, avisos, tareas, monitores
│       │   ├── finanzas/             # FINANZAS: liquidaciones, grilla salarial, facturas
│       │   └── admin/                # ADMIN: estructura académica, usuarios, auditoría
│       └── shared/
│           ├── services/api.ts       # Axios centralizado con interceptor de auth
│           └── components/           # Componentes reutilizables (Spinner, AppShell…)
│
├── knowledge-base/                   # Documentación de dominio (fuente de verdad)
├── docs/                             # Arquitectura y PRD
├── docker-compose.yml
└── README.md
```

---

## API Reference

La documentación interactiva completa está disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints principales

| Grupo | Base path | Descripción |
|---|---|---|
| Auth | `/api/v1/auth` | Login, refresh, logout, 2FA, recuperación de contraseña |
| Usuarios | `/api/v1/usuarios` | ABM de usuarios del tenant |
| Carreras | `/api/v1/carreras` | Estructura académica |
| Cohortes | `/api/v1/cohortes` | Ciclos lectivos |
| Materias | `/api/v1/materias` | Catálogo de materias |
| Equipos | `/api/v1/equipos` | Equipos docentes |
| Padrón | `/api/v1/padron` | Import de alumnos (xlsx/csv + Moodle) |
| Calificaciones | `/api/v1/calificaciones` | Import y umbral de aprobación |
| Análisis | `/api/v1/analisis` | Atrasados, ranking, notas finales |
| Comunicaciones | `/api/v1/comunicaciones` | Cola de mensajes a alumnos |
| Encuentros | `/api/v1/encuentros` | Slots e instancias de encuentro |
| Guardias | `/api/v1/guardias` | Registro de guardias docentes |
| Coloquios | `/api/v1/coloquios` | Convocatorias, reservas, resultados |
| Avisos | `/api/v1/avisos` | Publicación y acknowledgment |
| Tareas | `/api/v1/tareas` | Tareas internas con workflow |
| Programas | `/api/v1/programas` | Programas de materias |
| Liquidaciones | `/api/v1/liquidaciones` | Cálculo y cierre de honorarios |
| Facturas | `/api/v1/facturas` | Gestión de facturas de docentes |
| Auditoría | `/api/v1/auditoria` | Panel de métricas y log completo |
| Perfil | `/api/v1/perfil` | Edición del perfil propio |
| Inbox | `/api/v1/inbox` | Mensajería interna entre usuarios |
| Health | `/health` | Estado del servicio |

### Autenticación

Todos los endpoints (excepto `/health` y `/api/v1/auth/login`) requieren el header:

```
Authorization: Bearer <access_token>
```

El access token expira en **15 minutos**. Renovarlo con:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{ "refresh_token": "<refresh_token>" }
```

---

## Roles y permisos

El sistema usa **RBAC fino por `modulo:accion`**. Fail-closed: sin permiso explícito → 403.

| Rol | Descripción principal |
|---|---|
| `ALUMNO` | Acceso a sus propias calificaciones y reserva de coloquios |
| `TUTOR` | Seguimiento de alumnos asignados |
| `PROFESOR` | Gestión de comisiones, importación, comunicaciones |
| `COORDINADOR` | Equipos docentes, avisos, configuración académica |
| `NEXO` | Enlace administrativo con tratamiento contable diferenciado |
| `ADMIN` | Administración completa del tenant |
| `FINANZAS` | Liquidaciones, facturas, grilla salarial |

Los permisos efectivos se resuelven server-side por request (unión de roles × vigencia de asignación × tenant).

---

## Variables de entorno

Crear `backend/.env` basándose en:

```env
# ── Base de datos ────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace
DATABASE_URL_TEST=postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test

# ── Seguridad ────────────────────────────────────────────────────────────────
# Mínimo 32 caracteres. Generá con: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=cambia-esto-por-una-clave-segura-de-minimo-32-caracteres

# Exactamente 64 hex chars (32 bytes AES-256). Generá con: python -c "import secrets; print(secrets.token_hex(32))"
ENCRYPTION_KEY=0000000000000000000000000000000000000000000000000000000000000000

# Minutos de vida del access token (default: 15)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# ── Observabilidad (opcional) ────────────────────────────────────────────────
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=activia-trace-api
```

> **Nunca commitear `.env` con valores reales.** El archivo `.env.example` es la referencia segura.

---

## Deploy en producción (Easypanel)

El `Dockerfile` usa **multi-stage build** optimizado para producción:

- **Stage `builder`**: instala dependencias con `uv` (rápido y determinístico)
- **Stage `runtime`**: imagen mínima `python:3.13-slim`, sin build toolchain, usuario no-root

### Pasos en Easypanel

1. Conectar el repositorio GitHub
2. Configurar el servicio `api`:
   - **Build context**: `./backend`
   - **Dockerfile**: `Dockerfile`
   - **Target stage**: `runtime`
   - **Port**: `8000`
3. Configurar el servicio `worker`:
   - Mismo build que `api`
   - **Command override**: `python -m app.workers.main`
4. Agregar servicio `postgres:16-alpine` con volumen persistente
5. Setear todas las variables de entorno de producción (nunca reutilizar las de desarrollo)
6. Ejecutar migraciones tras el primer deploy:
   ```bash
   alembic upgrade head
   ```

---

## Decisiones de diseño relevantes

| Decisión | Detalle |
|---|---|
| **Multi-tenancy row-level** | `tenant_id` en cada tabla; repositories filtran por defecto. Un query sin scope es un bug. |
| **Identidad solo del JWT** | Nunca de parámetros de URL, body ni headers. El token define quién es el usuario y a qué tenant pertenece. |
| **Soft delete universal** | Ninguna entidad se borra físicamente. Auditoría append-only. |
| **PII cifrada en reposo** | CUIL, CBU, DNI con AES-256-GCM. Passwords con Argon2id. Nunca texto plano. |
| **Tests sin mocks de DB** | PostgreSQL real en tests de integración. Mockear la DB no prueba nada. |
| **Una migración por cambio** | Convención estricta. Downgrade siempre implementado. |
| **Strict TDD** | Test falla → código mínimo → triangulación → refactor. Sin código de producción sin test previo. |

---

## Licencia

Proyecto académico — Universidad. No distribuir sin autorización.
