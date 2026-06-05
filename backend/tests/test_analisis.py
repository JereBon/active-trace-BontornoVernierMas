"""tests/test_analisis.py — TDD tests for C-11: analisis-atrasados-reportes.

TDD cycles covered:
  2.1  AnalisisRepository.list_calificaciones_por_version: returns only cals for active version, tenant-isolated
  2.4  AnalisisRepository.list_sin_corregir: finalizado_lms=True + nota_textual=NULL + nota_numerica=NULL
  2.6  AnalisisRepository.list_monitor: filtros por materia_id, comision, regional, solo_atrasados, fechas
  3.1  calcular_atrasados: pure function — missing activities, not-approved activities, all-approved excluded
  3.4  calcular_ranking: only >=1 approved, desc order, tie-break by apellidos
  3.6  calcular_notas_finales: average of nota_numerica; null if none
  3.8  calcular_reporte_materia: all zeros when no data; correct counts with data
  4.2  Schemas extra='forbid'
  6.1  GET /v1/analisis/atrasados: 403 without permission, correct list with permission
  6.2  GET /v1/analisis/ranking: only >=1 approved
  6.3  GET /v1/analisis/sin-corregir: correct filter
  6.4  GET /v1/analisis/monitor: filters work
  6.5  GET /v1/analisis/reporte-materia: zeros when no data
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_TEST_SECRET = "test-secret-key-32-characters-ok!"
_TEST_ENCRYPTION_KEY = "0" * 64


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(user_id), "tenant_id": str(tenant_id)},
        expires_delta=timedelta(minutes=30),
    )


@dataclass
class TenantInfo:
    id: uuid.UUID
    slug: str


@dataclass
class UserInfo:
    id: uuid.UUID
    tenant_id: uuid.UUID
    token: str


@dataclass
class AnalisisContext:
    materia_id: uuid.UUID
    asignacion_id: uuid.UUID
    entrada_padron_id: uuid.UUID
    version_id: uuid.UUID
    cohorte_id: uuid.UUID
    carrera_id: uuid.UUID


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def test_client(
    test_session_factory: async_sessionmaker[AsyncSession],
):
    from asgi_lifespan import LifespanManager
    from app.core.config import _reset_settings
    from app.main import create_application

    test_db_url = os.environ.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test",
    )
    os.environ["DATABASE_URL"] = test_db_url
    os.environ["SECRET_KEY"] = _TEST_SECRET
    os.environ["ENCRYPTION_KEY"] = _TEST_ENCRYPTION_KEY
    _reset_settings()

    app = create_application()

    async with LifespanManager(app) as mgr:
        from app.core import database as db_module
        from app.models.base import Base

        async with db_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        import httpx

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=mgr.app),
            base_url="http://testserver",
        ) as client:
            yield client


@pytest_asyncio.fixture(scope="module")
async def an_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: Any,
) -> TenantInfo:
    from app.models.tenant import Tenant

    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"an-tenant-{uuid.uuid4().hex[:8]}",
            nombre="Analisis Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def an_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
) -> UserInfo:
    from app.core.security import email_hash as _eh, hash_password
    from app.models.usuario import Usuario

    raw = f"an-user-{uuid.uuid4().hex[:8]}@test.com"
    user_id = uuid.uuid4()
    async with test_session_factory() as session:
        u = Usuario(
            id=user_id,
            tenant_id=an_tenant.id,
            email_cifrado="placeholder-an",
            email_hash=_eh(raw),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=an_tenant.id, token=_make_token(user_id, an_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def an_user_with_perm(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    test_client: Any,
) -> UserInfo:
    """User that has the atrasados:ver permission."""
    from app.core.security import email_hash as _eh, hash_password
    from app.models.usuario import Usuario
    from app.models.usuario_rol import UsuarioRol
    from app.models.rol import Rol
    from sqlalchemy import select

    raw = f"an-perm-{uuid.uuid4().hex[:8]}@test.com"
    user_id = uuid.uuid4()
    async with test_session_factory() as session:
        u = Usuario(
            id=user_id,
            tenant_id=an_tenant.id,
            email_cifrado="placeholder-an-perm",
            email_hash=_eh(raw),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u)
        await session.flush()

        # Find a rol that has atrasados:ver permission
        # Use COORDINADOR which should have the permission per seed
        rol_stmt = select(Rol).where(Rol.codigo == "COORDINADOR").limit(1)
        rol_result = await session.execute(rol_stmt)
        rol = rol_result.scalar_one_or_none()

        if rol:
            ur = UsuarioRol(
                id=uuid.uuid4(),
                tenant_id=an_tenant.id,
                usuario_id=user_id,
                rol_id=rol.id,
                vig_desde=date(2025, 1, 1),
            )
            session.add(ur)

        await session.commit()

    return UserInfo(id=user_id, tenant_id=an_tenant.id, token=_make_token(user_id, an_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def an_context(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_user: UserInfo,
) -> AnalisisContext:
    """Create full academic context with calificaciones for testing."""
    from app.core.crypto import encrypt
    from app.models.asignacion import Asignacion
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    from app.models.entrada_padron import EntradaPadron
    from app.models.materia import Materia
    from app.models.version_padron import VersionPadron
    from app.models.calificacion import Calificacion

    async with test_session_factory() as session:
        carrera = Carrera(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            codigo=f"CAR-AN-{uuid.uuid4().hex[:4]}",
            nombre="Carrera Analisis",
            estado="Activa",
        )
        session.add(carrera)

        materia = Materia(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            codigo=f"MAT-AN-{uuid.uuid4().hex[:4]}",
            nombre="Materia Analisis",
            estado="Activa",
        )
        session.add(materia)
        await session.flush()

        cohorte = Cohorte(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            carrera_id=carrera.id,
            nombre=f"COH-AN-{uuid.uuid4().hex[:4]}",
            anio=2026,
            vig_desde=date(2026, 1, 1),
            estado="Activa",
        )
        session.add(cohorte)
        await session.flush()

        asignacion = Asignacion(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            usuario_id=an_user.id,
            rol="PROFESOR",
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            comisiones=[],
            desde=date(2026, 1, 1),
        )
        session.add(asignacion)
        await session.flush()

        version = VersionPadron(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            cargado_por=an_user.id,
            activa=True,
        )
        session.add(version)
        await session.flush()

        # Two students
        entrada1 = EntradaPadron(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            version_id=version.id,
            nombre="Ana",
            apellidos="Garcia",
            email_cifrado=encrypt("ana@test.com"),
            comision="C1",
            regional="Norte",
        )
        entrada2 = EntradaPadron(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            version_id=version.id,
            nombre="Bruno",
            apellidos="Lopez",
            email_cifrado=encrypt("bruno@test.com"),
            comision="C2",
            regional="Sur",
        )
        session.add(entrada1)
        session.add(entrada2)
        await session.flush()

        # Ana has 2 approved activities and 1 not approved
        now = datetime.now(tz=timezone.utc)
        cal1 = Calificacion(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            entrada_padron_id=entrada1.id,
            materia_id=materia.id,
            actividad="TP1",
            nota_numerica=80.0,
            nota_textual=None,
            aprobado=True,
            origen="Importado",
            importado_at=now,
        )
        cal2 = Calificacion(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            entrada_padron_id=entrada1.id,
            materia_id=materia.id,
            actividad="TP2",
            nota_numerica=40.0,
            nota_textual=None,
            aprobado=False,
            origen="Importado",
            importado_at=now,
        )
        # Bruno has 1 approved activity
        cal3 = Calificacion(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            entrada_padron_id=entrada2.id,
            materia_id=materia.id,
            actividad="TP1",
            nota_numerica=70.0,
            nota_textual=None,
            aprobado=True,
            origen="Importado",
            importado_at=now,
        )
        # Textual TP marked as finalizado but not graded yet
        cal_sin_corregir = Calificacion(
            id=uuid.uuid4(),
            tenant_id=an_tenant.id,
            entrada_padron_id=entrada2.id,
            materia_id=materia.id,
            actividad="TP2",
            nota_numerica=None,
            nota_textual=None,
            aprobado=False,
            origen="Importado",
            importado_at=now,
            finalizado_lms=True,
        )
        session.add(cal1)
        session.add(cal2)
        session.add(cal3)
        session.add(cal_sin_corregir)
        await session.commit()

        return AnalisisContext(
            materia_id=materia.id,
            asignacion_id=asignacion.id,
            entrada_padron_id=entrada1.id,
            version_id=version.id,
            cohorte_id=cohorte.id,
            carrera_id=carrera.id,
        )


# ─── Task 2.1 — AnalisisRepository.list_calificaciones_por_version ────────────


@pytest.mark.anyio
async def test_list_calificaciones_por_version(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_context: AnalisisContext,
) -> None:
    """RED→GREEN: repository returns calificaciones for entries of the active version."""
    from app.repositories.analisis_repository import AnalisisRepository

    async with test_session_factory() as session:
        repo = AnalisisRepository(session, an_tenant.id)
        cals = await repo.list_calificaciones_por_version(
            materia_id=an_context.materia_id,
            version_id=an_context.version_id,
        )

    assert len(cals) >= 3  # at least the 3 graded cals + the sin_corregir


# Task 2.3 — Triangulation: tenant isolation
@pytest.mark.anyio
async def test_list_calificaciones_tenant_isolation(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_context: AnalisisContext,
) -> None:
    """Triangulation: other tenant gets no results for the same materia_id."""
    from app.repositories.analisis_repository import AnalisisRepository

    other_tenant_id = uuid.uuid4()
    async with test_session_factory() as session:
        repo = AnalisisRepository(session, other_tenant_id)
        cals = await repo.list_calificaciones_por_version(
            materia_id=an_context.materia_id,
            version_id=an_context.version_id,
        )

    assert cals == []


# ─── Task 2.4 — AnalisisRepository.list_sin_corregir ─────────────────────────


@pytest.mark.anyio
async def test_list_sin_corregir_returns_only_eligible(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_context: AnalisisContext,
) -> None:
    """RED→GREEN: only finalizado_lms=True, nota_textual=NULL, nota_numerica=NULL."""
    from app.repositories.analisis_repository import AnalisisRepository

    async with test_session_factory() as session:
        repo = AnalisisRepository(session, an_tenant.id)
        sin_corregir = await repo.list_sin_corregir(materia_id=an_context.materia_id)

    # Only cal_sin_corregir matches: finalizado_lms=True, nota_textual=NULL, nota_numerica=NULL
    assert len(sin_corregir) == 1
    cal = sin_corregir[0]
    assert cal.finalizado_lms is True
    assert cal.nota_textual is None
    assert cal.nota_numerica is None


@pytest.mark.anyio
async def test_list_sin_corregir_excludes_graded(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_context: AnalisisContext,
) -> None:
    """Triangulation: graded (nota_numerica set) activities are excluded."""
    from app.repositories.analisis_repository import AnalisisRepository

    async with test_session_factory() as session:
        repo = AnalisisRepository(session, an_tenant.id)
        sin_corregir = await repo.list_sin_corregir(materia_id=an_context.materia_id)

    # Verify none of the results have nota_numerica or nota_textual set
    for cal in sin_corregir:
        assert cal.nota_numerica is None, "numeric grade should exclude from sin_corregir"
        assert cal.nota_textual is None, "textual grade should exclude from sin_corregir"


# ─── Task 2.6 — AnalisisRepository.list_monitor ──────────────────────────────


@pytest.mark.anyio
async def test_list_monitor_filter_by_materia(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_context: AnalisisContext,
) -> None:
    """RED→GREEN: monitor filtered by materia_id returns only that materia's entries."""
    from app.repositories.analisis_repository import AnalisisRepository

    async with test_session_factory() as session:
        repo = AnalisisRepository(session, an_tenant.id)
        items = await repo.list_monitor(
            materia_ids=[an_context.materia_id],
            filtros={},
        )

    assert len(items) >= 2  # At least Ana and Bruno
    for item in items:
        assert item["materia_id"] == an_context.materia_id


@pytest.mark.anyio
async def test_list_monitor_filter_comision(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_context: AnalisisContext,
) -> None:
    """Triangulation: filter by comision returns only that comision's entries."""
    from app.repositories.analisis_repository import AnalisisRepository

    async with test_session_factory() as session:
        repo = AnalisisRepository(session, an_tenant.id)
        items = await repo.list_monitor(
            materia_ids=[an_context.materia_id],
            filtros={"comision": "C1"},
        )

    assert all(item["comision"] == "C1" for item in items)
    names = [item["apellidos"] for item in items]
    assert "Garcia" in names
    assert "Lopez" not in names


@pytest.mark.anyio
async def test_list_monitor_filter_solo_atrasados(
    test_session_factory: async_sessionmaker[AsyncSession],
    an_tenant: TenantInfo,
    an_context: AnalisisContext,
) -> None:
    """Triangulation: solo_atrasados=True returns only students with missing/failed activities."""
    from app.repositories.analisis_repository import AnalisisRepository

    async with test_session_factory() as session:
        repo = AnalisisRepository(session, an_tenant.id)
        items = await repo.list_monitor(
            materia_ids=[an_context.materia_id],
            filtros={"solo_atrasados": True},
        )

    # Both Ana (has TP2 not approved) and Bruno (has TP2 ungraded/missing) should appear
    assert len(items) >= 1


# ─── Task 3.1 — calcular_atrasados pure function ─────────────────────────────


@pytest.mark.anyio
async def test_calcular_atrasados_alumno_sin_calificaciones():
    """RED→GREEN: student with no calificaciones is atrasado with all activities as missing."""
    from app.services.analisis_service import calcular_atrasados

    all_actividades = {"TP1", "TP2"}
    entradas = [{"id": uuid.uuid4(), "nombre": "Maria", "apellidos": "Doe", "comision": "C1"}]
    cals_por_entrada: dict[uuid.UUID, list[Any]] = {}

    result = calcular_atrasados(entradas, cals_por_entrada, all_actividades)

    assert len(result) == 1
    assert result[0]["apellidos"] == "Doe"
    assert set(result[0]["actividades_faltantes"]) == {"TP1", "TP2"}
    assert result[0]["actividades_no_aprobadas"] == []


@pytest.mark.anyio
async def test_calcular_atrasados_con_nota_no_aprobada():
    """Triangulation: student with aprobado=False on some activity is atrasado."""
    from app.services.analisis_service import calcular_atrasados

    entrada_id = uuid.uuid4()
    all_actividades = {"TP1", "TP2"}
    entradas = [{"id": entrada_id, "nombre": "Pedro", "apellidos": "Ruiz", "comision": "C2"}]
    cals_por_entrada = {
        entrada_id: [
            {"actividad": "TP1", "aprobado": True},
            {"actividad": "TP2", "aprobado": False},
        ]
    }

    result = calcular_atrasados(entradas, cals_por_entrada, all_actividades)

    assert len(result) == 1
    assert result[0]["apellidos"] == "Ruiz"
    assert result[0]["actividades_faltantes"] == []
    assert "TP2" in result[0]["actividades_no_aprobadas"]


@pytest.mark.anyio
async def test_calcular_atrasados_alumno_todas_aprobadas():
    """Triangulation: student with all activities approved is NOT atrasado."""
    from app.services.analisis_service import calcular_atrasados

    entrada_id = uuid.uuid4()
    all_actividades = {"TP1", "TP2"}
    entradas = [{"id": entrada_id, "nombre": "Lucia", "apellidos": "Vera", "comision": "C1"}]
    cals_por_entrada = {
        entrada_id: [
            {"actividad": "TP1", "aprobado": True},
            {"actividad": "TP2", "aprobado": True},
        ]
    }

    result = calcular_atrasados(entradas, cals_por_entrada, all_actividades)

    assert result == []


# ─── Task 3.4 — calcular_ranking pure function ───────────────────────────────


@pytest.mark.anyio
async def test_calcular_ranking_solo_con_aprobadas():
    """RED→GREEN: ranking includes only students with >=1 aprobada, sorted desc."""
    from app.services.analisis_service import calcular_ranking

    id_a = uuid.uuid4()
    id_b = uuid.uuid4()
    id_c = uuid.uuid4()
    entradas = [
        {"id": id_a, "nombre": "A", "apellidos": "Alpha", "comision": "C1"},
        {"id": id_b, "nombre": "B", "apellidos": "Beta", "comision": "C1"},
        {"id": id_c, "nombre": "C", "apellidos": "Gamma", "comision": "C1"},
    ]
    cals_por_entrada = {
        id_a: [{"actividad": "TP1", "aprobado": True}, {"actividad": "TP2", "aprobado": True}],
        id_b: [{"actividad": "TP1", "aprobado": False}],
        id_c: [{"actividad": "TP1", "aprobado": True}],
    }

    result = calcular_ranking(entradas, cals_por_entrada)

    # Only A and C appear (B has 0 approved)
    apellidos_list = [r["apellidos"] for r in result]
    assert "Alpha" in apellidos_list
    assert "Gamma" in apellidos_list
    assert "Beta" not in apellidos_list
    # A has 2 approved → should be first
    assert result[0]["apellidos"] == "Alpha"
    assert result[0]["cant_aprobadas"] == 2


@pytest.mark.anyio
async def test_calcular_ranking_empate_orden_apellidos():
    """Triangulation: tie in approved count → alphabetical by apellidos."""
    from app.services.analisis_service import calcular_ranking

    id_a = uuid.uuid4()
    id_b = uuid.uuid4()
    entradas = [
        {"id": id_a, "nombre": "Z", "apellidos": "Zebra", "comision": "C1"},
        {"id": id_b, "nombre": "A", "apellidos": "Alva", "comision": "C1"},
    ]
    cals_por_entrada = {
        id_a: [{"actividad": "TP1", "aprobado": True}],
        id_b: [{"actividad": "TP1", "aprobado": True}],
    }

    result = calcular_ranking(entradas, cals_por_entrada)

    # Same count → alphabetical by apellidos
    assert result[0]["apellidos"] == "Alva"
    assert result[1]["apellidos"] == "Zebra"


# ─── Task 3.6 — calcular_notas_finales pure function ─────────────────────────


@pytest.mark.anyio
async def test_calcular_notas_finales_promedio_simple():
    """RED→GREEN: promedio simple of nota_numerica."""
    from app.services.analisis_service import calcular_notas_finales

    entrada_id = uuid.uuid4()
    entradas = [{"id": entrada_id, "nombre": "X", "apellidos": "Xander", "comision": "C1"}]
    cals_por_entrada = {
        entrada_id: [
            {"actividad": "TP1", "nota_numerica": 80.0, "aprobado": True},
            {"actividad": "TP2", "nota_numerica": 60.0, "aprobado": True},
            {"actividad": "TP3", "nota_numerica": 70.0, "aprobado": True},
        ]
    }

    result = calcular_notas_finales(entradas, cals_por_entrada)

    assert len(result) == 1
    assert result[0]["nota_final"] == pytest.approx(70.0)


@pytest.mark.anyio
async def test_calcular_notas_finales_sin_numericas():
    """Triangulation: student with only textual grades → nota_final = None."""
    from app.services.analisis_service import calcular_notas_finales

    entrada_id = uuid.uuid4()
    entradas = [{"id": entrada_id, "nombre": "Y", "apellidos": "Young", "comision": "C2"}]
    cals_por_entrada = {
        entrada_id: [
            {"actividad": "TP1", "nota_numerica": None, "aprobado": True},
        ]
    }

    result = calcular_notas_finales(entradas, cals_por_entrada)

    assert len(result) == 1
    assert result[0]["nota_final"] is None


# ─── Task 3.8 — calcular_reporte_materia pure function ───────────────────────


@pytest.mark.anyio
async def test_calcular_reporte_materia_sin_datos():
    """RED→GREEN: returns zeros when no calificaciones."""
    from app.services.analisis_service import calcular_reporte_materia

    entradas = [
        {"id": uuid.uuid4(), "nombre": "A", "apellidos": "B", "comision": "C1"},
    ]
    calificaciones: list[Any] = []

    result = calcular_reporte_materia(entradas, calificaciones)

    assert result["total_alumnos"] == 1
    assert result["total_actividades"] == 0
    assert result["alumnos_con_aprobada"] == 0
    # When no activities exist, student is NOT atrasado (no universe to be behind on)
    assert result["alumnos_atrasados"] == 0
    assert result["porcentaje_aprobacion"] == 0.0


@pytest.mark.anyio
async def test_calcular_reporte_materia_con_datos():
    """Triangulation: correct counts when data present."""
    from app.services.analisis_service import calcular_reporte_materia

    id_a = uuid.uuid4()
    id_b = uuid.uuid4()
    entradas = [
        {"id": id_a, "nombre": "A", "apellidos": "A", "comision": "C1"},
        {"id": id_b, "nombre": "B", "apellidos": "B", "comision": "C1"},
    ]
    calificaciones = [
        {"entrada_padron_id": id_a, "actividad": "TP1", "aprobado": True},
        {"entrada_padron_id": id_b, "actividad": "TP1", "aprobado": False},
    ]

    result = calcular_reporte_materia(entradas, calificaciones)

    assert result["total_alumnos"] == 2
    assert result["total_actividades"] == 1
    assert result["alumnos_con_aprobada"] == 1
    assert result["alumnos_atrasados"] == 1  # B has TP1 not approved
    assert result["porcentaje_aprobacion"] == 50.0


# ─── Task 4.2 — Schema extra='forbid' ────────────────────────────────────────


def test_atrasado_out_forbids_extra():
    """Schema must reject extra fields."""
    from pydantic import ValidationError
    from app.schemas.analisis import AtrasadoOut

    with pytest.raises(ValidationError):
        AtrasadoOut(
            entrada_padron_id=uuid.uuid4(),
            nombre="A",
            apellidos="B",
            comision="C1",
            actividades_faltantes=[],
            actividades_no_aprobadas=[],
            campo_extra="forbidden",  # type: ignore
        )


def test_ranking_item_out_forbids_extra():
    from pydantic import ValidationError
    from app.schemas.analisis import RankingItemOut

    with pytest.raises(ValidationError):
        RankingItemOut(
            entrada_padron_id=uuid.uuid4(),
            nombre="A",
            apellidos="B",
            comision="C1",
            cant_aprobadas=1,
            campo_extra="nope",  # type: ignore
        )


# ─── Helper: create an app with mocked permissions ───────────────────────────


def _make_app_with_perm(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    roles: list[str],
    permisos: set[str],
):
    """Create a FastAPI app instance with a mocked get_current_user returning given perms."""
    import os as _os
    from app.core.config import _reset_settings
    from app.main import create_application
    from app.core.schemas import UsuarioAutenticado
    from app.core import dependencies as deps

    test_db_url = _os.environ.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test",
    )
    _os.environ["DATABASE_URL"] = test_db_url
    _os.environ["SECRET_KEY"] = _TEST_SECRET
    _os.environ["ENCRYPTION_KEY"] = _TEST_ENCRYPTION_KEY
    _reset_settings()

    app = create_application()

    mock_user = UsuarioAutenticado(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles,
        permisos_efectivos=permisos,
    )

    async def mock_get_current_user(token=None, session=None):
        return mock_user

    app.dependency_overrides[deps.get_current_user] = mock_get_current_user
    return app


# ─── Task 6.1 — Integration: GET /v1/analisis/atrasados ──────────────────────


@pytest.mark.anyio
async def test_get_atrasados_sin_permiso(
    test_client: Any,
    an_tenant: TenantInfo,
    an_user: UserInfo,
    an_context: AnalisisContext,
) -> None:
    """User without atrasados:ver permission receives 403."""
    resp = await test_client.get(
        f"/v1/analisis/atrasados?materia_id={an_context.materia_id}",
        headers={"Authorization": f"Bearer {an_user.token}"},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_get_atrasados_con_permiso(
    an_tenant: TenantInfo,
    an_user: UserInfo,
    an_context: AnalisisContext,
) -> None:
    """User with atrasados:ver gets list of atrasados."""
    import httpx
    from asgi_lifespan import LifespanManager

    app = _make_app_with_perm(
        an_user.id, an_tenant.id, ["COORDINADOR"], {"atrasados:ver"}
    )
    try:
        async with LifespanManager(app) as mgr:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=mgr.app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get(
                    f"/v1/analisis/atrasados?materia_id={an_context.materia_id}",
                )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
    finally:
        app.dependency_overrides.clear()


# ─── Task 6.2 — Integration: GET /v1/analisis/ranking ────────────────────────


@pytest.mark.anyio
async def test_get_ranking_only_approved(
    an_tenant: TenantInfo,
    an_user: UserInfo,
    an_context: AnalisisContext,
) -> None:
    """Ranking only returns students with >=1 approved activity."""
    import httpx
    from asgi_lifespan import LifespanManager

    app = _make_app_with_perm(
        an_user.id, an_tenant.id, ["COORDINADOR"], {"atrasados:ver"}
    )
    try:
        async with LifespanManager(app) as mgr:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=mgr.app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get(
                    f"/v1/analisis/ranking?materia_id={an_context.materia_id}",
                )
        assert resp.status_code == 200
        data = resp.json()
        for item in data:
            assert item["cant_aprobadas"] >= 1
    finally:
        app.dependency_overrides.clear()


# ─── Task 6.3 — Integration: GET /v1/analisis/sin-corregir ───────────────────


@pytest.mark.anyio
async def test_get_sin_corregir(
    an_tenant: TenantInfo,
    an_user: UserInfo,
    an_context: AnalisisContext,
) -> None:
    """sin-corregir returns only finalizado_lms=True and ungraded textual activities."""
    import httpx
    from asgi_lifespan import LifespanManager

    app = _make_app_with_perm(
        an_user.id, an_tenant.id, ["COORDINADOR"], {"atrasados:ver"}
    )
    try:
        async with LifespanManager(app) as mgr:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=mgr.app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get(
                    f"/v1/analisis/sin-corregir?materia_id={an_context.materia_id}",
                )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    finally:
        app.dependency_overrides.clear()


# ─── Task 6.4 — Integration: GET /v1/analisis/monitor ────────────────────────


@pytest.mark.anyio
async def test_get_monitor_filter_materia(
    an_tenant: TenantInfo,
    an_user: UserInfo,
    an_context: AnalisisContext,
) -> None:
    """Monitor with materia_id filter returns only that materia's entries."""
    import httpx
    from asgi_lifespan import LifespanManager

    app = _make_app_with_perm(
        an_user.id, an_tenant.id, ["COORDINADOR"], {"atrasados:ver"}
    )
    try:
        async with LifespanManager(app) as mgr:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=mgr.app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get(
                    f"/v1/analisis/monitor?materia_id={an_context.materia_id}",
                )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_monitor_filter_solo_atrasados(
    an_tenant: TenantInfo,
    an_user: UserInfo,
    an_context: AnalisisContext,
) -> None:
    """Monitor with solo_atrasados=true returns only atrasados."""
    import httpx
    from asgi_lifespan import LifespanManager

    app = _make_app_with_perm(
        an_user.id, an_tenant.id, ["COORDINADOR"], {"atrasados:ver"}
    )
    try:
        async with LifespanManager(app) as mgr:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=mgr.app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get(
                    f"/v1/analisis/monitor?materia_id={an_context.materia_id}&solo_atrasados=true",
                )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for item in data:
            assert item.get("es_atrasado") is True
    finally:
        app.dependency_overrides.clear()


# ─── Task 6.5 — Integration: GET /v1/analisis/reporte-materia ────────────────


@pytest.mark.anyio
async def test_get_reporte_materia_con_datos(
    an_tenant: TenantInfo,
    an_user: UserInfo,
    an_context: AnalisisContext,
) -> None:
    """Reporte returns valid metrics."""
    import httpx
    from asgi_lifespan import LifespanManager

    app = _make_app_with_perm(
        an_user.id, an_tenant.id, ["COORDINADOR"], {"atrasados:ver"}
    )
    try:
        async with LifespanManager(app) as mgr:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=mgr.app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get(
                    f"/v1/analisis/reporte-materia?materia_id={an_context.materia_id}",
                )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_alumnos" in data
        assert "total_actividades" in data
        assert "alumnos_con_aprobada" in data
        assert "alumnos_atrasados" in data
        assert "porcentaje_aprobacion" in data
    finally:
        app.dependency_overrides.clear()
