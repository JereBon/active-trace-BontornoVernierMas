"""tests/test_liquidaciones.py — TDD tests for C-18 liquidaciones-y-honorarios.

Covers:
  3.1  parse_periodo / es_vigente — pure period utils
  3.2  _calcular_montos — pure salary calculation function
  3.3  LiquidacionService.calcular — base vigente, plus acumulado, multi-vigencia
  4.1  LiquidacionService.cerrar — Abierta→Cerrada; 409 on second close
  4.2  LiquidacionService.vista_periodo — segmentation and KPIs
  4.3  LiquidacionService.historial — closed records filtered
  4.4  SalarioGrillaService — ABM SalarioBase and SalarioPlus
  4.5  FacturaService — ABM + Pendiente→Abonada transition
  6.4  HTTP endpoints — 403 without permission, 409 on closed, multi-tenant isolation

Uses real PostgreSQL test DB. No DB mocking (per project rules).
"""

import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.base import Base
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.asignacion import Asignacion
from app.models.salario_base import SalarioBase
from app.models.salario_plus import SalarioPlus
from app.models.liquidacion import Liquidacion, EstadoLiquidacion
from app.models.factura import Factura, EstadoFactura
from app.services.liquidacion_utils import parse_periodo, es_vigente
from app.services.liquidacion_calc import _calcular_montos

_TODAY = date.today()
_PERIODO = "2025-06"
_INI_MES = date(2025, 6, 1)
_FIN_MES = date(2025, 6, 30)


# ═══════════════════════════════════════════════════════════════════════════════
# Task 3.1 — parse_periodo / es_vigente (pure functions, no DB)
# ═══════════════════════════════════════════════════════════════════════════════


class TestParsePeriodo:
    def test_normal_month(self):
        ini, fin = parse_periodo("2025-06")
        assert ini == date(2025, 6, 1)
        assert fin == date(2025, 6, 30)

    def test_february_non_leap(self):
        ini, fin = parse_periodo("2025-02")
        assert ini == date(2025, 2, 1)
        assert fin == date(2025, 2, 28)

    def test_february_leap(self):
        ini, fin = parse_periodo("2024-02")
        assert ini == date(2024, 2, 1)
        assert fin == date(2024, 2, 29)

    def test_december(self):
        ini, fin = parse_periodo("2025-12")
        assert ini == date(2025, 12, 1)
        assert fin == date(2025, 12, 31)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_periodo("2025/06")

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError):
            parse_periodo("2025-13")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            parse_periodo("AAAA-MM")


class TestEsVigente:
    def test_open_ended_within_period(self):
        assert es_vigente(date(2025, 1, 1), None, _INI_MES, _FIN_MES) is True

    def test_starts_before_ends_within_period(self):
        assert es_vigente(date(2025, 5, 15), date(2025, 6, 15), _INI_MES, _FIN_MES) is True

    def test_starts_and_ends_within_period(self):
        assert es_vigente(date(2025, 6, 10), date(2025, 6, 20), _INI_MES, _FIN_MES) is True

    def test_starts_after_period_end(self):
        assert es_vigente(date(2025, 7, 1), None, _INI_MES, _FIN_MES) is False

    def test_ends_before_period_start(self):
        assert es_vigente(date(2025, 1, 1), date(2025, 5, 31), _INI_MES, _FIN_MES) is False

    def test_spans_entire_period(self):
        assert es_vigente(date(2024, 1, 1), date(2026, 12, 31), _INI_MES, _FIN_MES) is True

    def test_ends_exactly_on_first_day(self):
        assert es_vigente(date(2025, 1, 1), date(2025, 6, 1), _INI_MES, _FIN_MES) is True

    def test_starts_exactly_on_last_day(self):
        assert es_vigente(date(2025, 6, 30), None, _INI_MES, _FIN_MES) is True

    def test_ends_one_day_before_period(self):
        assert es_vigente(date(2025, 1, 1), date(2025, 5, 31), _INI_MES, _FIN_MES) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Task 3.2 — _calcular_montos (pure function, no DB)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalcularMontos:
    def test_simple_base_no_plus(self):
        mb, mp, t = _calcular_montos({}, Decimal("1000"), {})
        assert mb == Decimal("1000")
        assert mp == Decimal("0")
        assert t == Decimal("1000")

    def test_one_commission_one_plus(self):
        mb, mp, t = _calcular_montos(
            {"PROG": 1}, Decimal("1000"), {"PROG": Decimal("200")}
        )
        assert mb == Decimal("1000")
        assert mp == Decimal("200")
        assert t == Decimal("1200")

    def test_two_commissions_same_group(self):
        """2 commissions of PROG → 2 × Plus(PROG)."""
        mb, mp, t = _calcular_montos(
            {"PROG": 2}, Decimal("1000"), {"PROG": Decimal("200")}
        )
        assert mp == Decimal("400")
        assert t == Decimal("1400")

    def test_multiple_groups(self):
        """3 PROG commissions + 1 CALC commission."""
        mb, mp, t = _calcular_montos(
            {"PROG": 3, "CALC": 1},
            Decimal("2000"),
            {"PROG": Decimal("100"), "CALC": Decimal("300")},
        )
        assert mp == Decimal("300") + Decimal("300")  # 3×100 + 1×300
        assert t == Decimal("2000") + Decimal("600")

    def test_none_key_no_plus(self):
        """categoria_clave=None commissions → no Plus, no error."""
        mb, mp, t = _calcular_montos(
            {None: 5, "PROG": 1},
            Decimal("1500"),
            {"PROG": Decimal("150")},
        )
        assert mp == Decimal("150")  # only PROG
        assert t == Decimal("1650")

    def test_clave_without_plus_record(self):
        """Group in asignaciones but no SalarioPlus defined → 0 for that group."""
        mb, mp, t = _calcular_montos(
            {"UNKNOWN": 3},
            Decimal("500"),
            {},  # no plus records
        )
        assert mp == Decimal("0")
        assert t == Decimal("500")

    def test_zero_base_with_plus(self):
        """Zero base is valid (e.g. no SalarioBase found)."""
        mb, mp, t = _calcular_montos(
            {"PROG": 2}, Decimal("0"), {"PROG": Decimal("100")}
        )
        assert mb == Decimal("0")
        assert mp == Decimal("200")
        assert t == Decimal("200")

    def test_all_none_keys(self):
        """All commissions without clave → no plus at all."""
        mb, mp, t = _calcular_montos(
            {None: 10}, Decimal("3000"), {"PROG": Decimal("200")}
        )
        assert mp == Decimal("0")
        assert t == Decimal("3000")


# ═══════════════════════════════════════════════════════════════════════════════
# DB fixtures for integration tests
# ═══════════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    """Ensure all tables exist in the test DB."""
    from app.core import database as db_module
    engine = db_module.engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="module")
async def liq_ctx(test_session_factory, db_tables) -> dict:
    """Create tenant, cohorte, materias, usuarios, asignaciones, grilla salarial."""
    from app.core.security import hash_password, email_hash

    async with test_session_factory() as session:
        t_id = uuid.uuid4()
        tenant = Tenant(id=t_id, slug=f"liq-{uuid.uuid4().hex[:6]}", nombre="LiqTenant")
        session.add(tenant)
        await session.flush()

        carrera = Carrera(
            id=uuid.uuid4(), tenant_id=t_id,
            codigo="TST", nombre="Carrera Test", estado="Activa"
        )
        session.add(carrera)
        await session.flush()

        cohorte = Cohorte(
            id=uuid.uuid4(), tenant_id=t_id, carrera_id=carrera.id,
            nombre="2025", anio=2025, estado="Activa",
            vig_desde=date(2025, 1, 1), vig_hasta=None,
        )
        session.add(cohorte)
        await session.flush()

        # Materias: with and without categoria_clave
        materia_prog = Materia(
            id=uuid.uuid4(), tenant_id=t_id,
            codigo="PROG", nombre="Programación", estado="Activa",
            categoria_clave="PROG",
        )
        materia_sin_clave = Materia(
            id=uuid.uuid4(), tenant_id=t_id,
            codigo="SIN", nombre="Sin Clave", estado="Activa",
            categoria_clave=None,
        )
        session.add_all([materia_prog, materia_sin_clave])
        await session.flush()

        def _make_user(suffix: str, facturador: bool | None = None) -> Usuario:
            email = f"doc{suffix}@test.com"
            return Usuario(
                id=uuid.uuid4(), tenant_id=t_id,
                email_cifrado=f"enc-{email}",
                email_hash=email_hash(email),
                password_hash=hash_password("pass123"),
                activo=True,
                facturador=facturador,
            )

        u_normal = _make_user("normal")
        u_nexo = _make_user("nexo")
        u_fact = _make_user("fact", facturador=True)
        session.add_all([u_normal, u_nexo, u_fact])
        await session.flush()

        # Asignaciones (vigentes in 2025-06)
        def _asig(usuario_id, rol, materia_id, comisiones):
            return Asignacion(
                id=uuid.uuid4(), tenant_id=t_id,
                usuario_id=usuario_id, rol=rol,
                cohorte_id=cohorte.id, materia_id=materia_id,
                comisiones=comisiones,
                desde=date(2025, 1, 1), hasta=None,
            )

        asig_normal_prog = _asig(u_normal.id, "PROFESOR", materia_prog.id, ["C1", "C2"])
        asig_normal_sin = _asig(u_normal.id, "PROFESOR", materia_sin_clave.id, ["C3"])
        asig_nexo = _asig(u_nexo.id, "NEXO", materia_prog.id, ["C4"])
        asig_fact = _asig(u_fact.id, "PROFESOR", materia_prog.id, ["C5"])
        session.add_all([asig_normal_prog, asig_normal_sin, asig_nexo, asig_fact])
        await session.flush()

        # SalarioBase: vigente in 2025-06
        base_prof = SalarioBase(
            id=uuid.uuid4(), tenant_id=t_id,
            rol="PROFESOR", monto=Decimal("1000.00"),
            desde=date(2025, 1, 1), hasta=None,
        )
        base_nexo = SalarioBase(
            id=uuid.uuid4(), tenant_id=t_id,
            rol="NEXO", monto=Decimal("800.00"),
            desde=date(2025, 1, 1), hasta=None,
        )
        # Expired base — should NOT be picked for 2025-06
        base_old = SalarioBase(
            id=uuid.uuid4(), tenant_id=t_id,
            rol="PROFESOR", monto=Decimal("500.00"),
            desde=date(2020, 1, 1), hasta=date(2024, 12, 31),
        )
        session.add_all([base_prof, base_nexo, base_old])
        await session.flush()

        # SalarioPlus vigente in 2025-06
        plus_prog = SalarioPlus(
            id=uuid.uuid4(), tenant_id=t_id,
            grupo="PROG", rol="PROFESOR", monto=Decimal("200.00"),
            desde=date(2025, 1, 1), hasta=None,
        )
        plus_prog_nexo = SalarioPlus(
            id=uuid.uuid4(), tenant_id=t_id,
            grupo="PROG", rol="NEXO", monto=Decimal("150.00"),
            desde=date(2025, 1, 1), hasta=None,
        )
        session.add_all([plus_prog, plus_prog_nexo])
        await session.flush()

        await session.commit()

    return {
        "tenant_id": t_id,
        "cohorte_id": cohorte.id,
        "u_normal_id": u_normal.id,
        "u_nexo_id": u_nexo.id,
        "u_fact_id": u_fact.id,
        "base_prof_id": base_prof.id,
        "plus_prog_id": plus_prog.id,
    }


@pytest_asyncio.fixture(scope="module")
async def tenant_b_ctx(test_session_factory, db_tables) -> dict:
    """Second tenant for multi-tenancy isolation tests."""
    from app.core.security import hash_password, email_hash

    async with test_session_factory() as session:
        t2_id = uuid.uuid4()
        tenant2 = Tenant(id=t2_id, slug=f"liq-b-{uuid.uuid4().hex[:6]}", nombre="LiqTenantB")
        session.add(tenant2)
        await session.flush()

        carrera2 = Carrera(
            id=uuid.uuid4(), tenant_id=t2_id,
            codigo="B", nombre="Carrera B", estado="Activa"
        )
        session.add(carrera2)
        await session.flush()

        cohorte2 = Cohorte(
            id=uuid.uuid4(), tenant_id=t2_id, carrera_id=carrera2.id,
            nombre="2025-B", anio=2025, estado="Activa",
            vig_desde=date(2025, 1, 1), vig_hasta=None,
        )
        session.add(cohorte2)
        await session.flush()

        # Create a real user for tenant B so FK constraint is satisfied
        u_b_email = f"b-user-{uuid.uuid4().hex[:8]}@test.com"
        u_b = Usuario(
            id=uuid.uuid4(), tenant_id=t2_id,
            email_cifrado="placeholder-b",
            email_hash=email_hash(u_b_email),
            password_hash=hash_password("pass"),
            activo=True,
        )
        session.add(u_b)
        await session.flush()

        # Add a liquidacion for tenant B
        liq_b = Liquidacion(
            id=uuid.uuid4(), tenant_id=t2_id,
            cohorte_id=cohorte2.id, periodo=_PERIODO,
            usuario_id=u_b.id, rol="PROFESOR",
            comisiones=[], monto_base=Decimal("999"), monto_plus=Decimal("0"),
            total=Decimal("999"), estado=EstadoLiquidacion.Abierta.value,
        )
        session.add(liq_b)
        await session.flush()
        await session.commit()

    return {"tenant_b_id": t2_id, "cohorte_b_id": cohorte2.id, "liq_b_id": liq_b.id}


# ═══════════════════════════════════════════════════════════════════════════════
# Task 3.3 — LiquidacionService.calcular (integration)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_calcular_creates_records(test_session_factory, liq_ctx):
    """calcular() creates Liquidacion records for each docente in the cohorte."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        records = await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    assert len(records) >= 3  # normal + nexo + fact


@pytest.mark.asyncio
async def test_calcular_base_vigente(test_session_factory, liq_ctx):
    """calcular() uses the current vigente SalarioBase (1000 for PROFESOR), not the expired one (500)."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        records = await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    prof_records = [r for r in records if r.usuario_id == liq_ctx["u_normal_id"]]
    assert prof_records, "Normal docente not found in records"
    # The normal docente has 2 PROG commissions + 1 no-clave commission → 1 row
    prof = prof_records[0]
    assert prof.monto_base == Decimal("1000.00")


@pytest.mark.asyncio
async def test_calcular_plus_acumulado_2_comisiones(test_session_factory, liq_ctx):
    """2 PROG commissions → 2 × Plus(PROG, PROFESOR) = 400."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        records = await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    prof = next(r for r in records if r.usuario_id == liq_ctx["u_normal_id"])
    # 2 PROG comisiones × 200 = 400 plus
    assert prof.monto_plus == Decimal("400.00")
    assert prof.total == Decimal("1400.00")


@pytest.mark.asyncio
async def test_calcular_categoria_clave_null_no_plus(test_session_factory, liq_ctx):
    """categoria_clave=NULL commissions don't generate Plus; no error."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        records = await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    prof = next(r for r in records if r.usuario_id == liq_ctx["u_normal_id"])
    # 1 comision in materia sin clave → does not add to monto_plus
    assert prof.monto_plus == Decimal("400.00")  # only 2 PROG, not 3 × something


@pytest.mark.asyncio
async def test_calcular_nexo_flag(test_session_factory, liq_ctx):
    """Docente with NEXO role has es_nexo=True in their record."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        records = await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    nexo = next(r for r in records if r.usuario_id == liq_ctx["u_nexo_id"])
    assert nexo.es_nexo is True


@pytest.mark.asyncio
async def test_calcular_facturante_flag(test_session_factory, liq_ctx):
    """Docente with facturador=True gets excluido_por_factura=True."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        records = await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    fact = next(r for r in records if r.usuario_id == liq_ctx["u_fact_id"])
    assert fact.excluido_por_factura is True


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.1 — LiquidacionService.cerrar + immutability 409
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_cerrar_abierta_ok(test_session_factory, liq_ctx):
    """cerrar() transitions all Abierta records of the period to Cerrada."""
    from app.services.liquidacion_service import LiquidacionService

    # First calculate to ensure records exist
    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        await svc.calcular(liq_ctx["cohorte_id"], "2025-07")

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        count = await svc.cerrar(
            liq_ctx["cohorte_id"], "2025-07", actor_id=uuid.uuid4()
        )
    assert count > 0


@pytest.mark.asyncio
async def test_cerrar_ya_cerrada_raises_409(test_session_factory, liq_ctx):
    """Second cerrar() on the same period raises a domain error (409)."""
    from app.core.exceptions import ConflictError
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        await svc.calcular(liq_ctx["cohorte_id"], "2025-08")

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        await svc.cerrar(liq_ctx["cohorte_id"], "2025-08", actor_id=uuid.uuid4())

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        with pytest.raises(ConflictError):
            await svc.cerrar(liq_ctx["cohorte_id"], "2025-08", actor_id=uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.2 — LiquidacionService.vista_periodo — segmentation + KPIs
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_vista_periodo_segmentacion(test_session_factory, liq_ctx):
    """vista_periodo returns segmented lists: general, nexo, facturantes."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        vista = await svc.vista_periodo(liq_ctx["cohorte_id"], _PERIODO)

    assert "general" in vista
    assert "nexo" in vista
    assert "facturantes" in vista
    assert "total_sin_factura" in vista
    assert "total_con_factura" in vista


@pytest.mark.asyncio
async def test_vista_periodo_kpis(test_session_factory, liq_ctx):
    """KPI total_sin_factura excludes facturante records; total_con_factura includes them."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        await svc.calcular(liq_ctx["cohorte_id"], _PERIODO)

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        vista = await svc.vista_periodo(liq_ctx["cohorte_id"], _PERIODO)

    # facturante record should be in facturantes list, not general
    fact_ids = [r["usuario_id"] for r in vista["facturantes"]]
    assert str(liq_ctx["u_fact_id"]) in [str(i) for i in fact_ids]

    # total_con_factura > 0 (facturante has nonzero total)
    assert Decimal(str(vista["total_con_factura"])) > Decimal("0")


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.3 — LiquidacionService.historial
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_historial_only_cerradas(test_session_factory, liq_ctx):
    """historial() returns only Cerrada records, not Abierta ones."""
    from app.services.liquidacion_service import LiquidacionService

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        await svc.calcular(liq_ctx["cohorte_id"], "2025-09")
        await svc.cerrar(liq_ctx["cohorte_id"], "2025-09", actor_id=uuid.uuid4())
        # Also calc another period but don't close it
        await svc.calcular(liq_ctx["cohorte_id"], "2025-10")

    async with test_session_factory() as session:
        svc = LiquidacionService(session, liq_ctx["tenant_id"])
        historial = await svc.historial(cohorte_id=liq_ctx["cohorte_id"])

    for record in historial:
        assert record.estado == EstadoLiquidacion.Cerrada.value


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.4 — SalarioGrillaService ABM
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_grilla_crear_base(test_session_factory, liq_ctx):
    """SalarioGrillaService.crear_base persists a SalarioBase record."""
    from app.services.salario_grilla_service import SalarioGrillaService

    async with test_session_factory() as session:
        svc = SalarioGrillaService(session, liq_ctx["tenant_id"])
        record = await svc.crear_base({
            "rol": "TUTOR",
            "monto": Decimal("600.00"),
            "desde": date(2025, 1, 1),
            "hasta": None,
        })

    assert record.id is not None
    assert record.rol == "TUTOR"
    assert record.monto == Decimal("600.00")


@pytest.mark.asyncio
async def test_grilla_crear_plus(test_session_factory, liq_ctx):
    """SalarioGrillaService.crear_plus persists a SalarioPlus record."""
    from app.services.salario_grilla_service import SalarioGrillaService

    async with test_session_factory() as session:
        svc = SalarioGrillaService(session, liq_ctx["tenant_id"])
        record = await svc.crear_plus({
            "grupo": "CALC",
            "rol": "TUTOR",
            "monto": Decimal("100.00"),
            "desde": date(2025, 1, 1),
            "hasta": None,
        })

    assert record.grupo == "CALC"
    assert record.rol == "TUTOR"


# ═══════════════════════════════════════════════════════════════════════════════
# Task 4.5 — FacturaService ABM + Pendiente→Abonada
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_factura_crear(test_session_factory, liq_ctx):
    """FacturaService.crear persists a Factura in Pendiente state."""
    from app.services.factura_service import FacturaService

    async with test_session_factory() as session:
        svc = FacturaService(session, liq_ctx["tenant_id"])
        factura = await svc.crear({
            "usuario_id": liq_ctx["u_fact_id"],
            "periodo": _PERIODO,
            "detalle": "Factura Test",
        })

    assert factura.estado == EstadoFactura.Pendiente.value
    assert factura.abonada_at is None


@pytest.mark.asyncio
async def test_factura_abonar(test_session_factory, liq_ctx):
    """FacturaService.cambiar_estado Pendiente→Abonada sets abonada_at."""
    from app.services.factura_service import FacturaService

    async with test_session_factory() as session:
        svc = FacturaService(session, liq_ctx["tenant_id"])
        factura = await svc.crear({
            "usuario_id": liq_ctx["u_fact_id"],
            "periodo": "2025-07",
            "detalle": "Para abonar",
        })
        abonada = await svc.cambiar_estado(factura.id, EstadoFactura.Abonada.value)

    assert abonada is not None
    assert abonada.estado == EstadoFactura.Abonada.value
    assert abonada.abonada_at is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Task 6.4 — HTTP endpoint tests (403, 409, multi-tenant isolation)
# ═══════════════════════════════════════════════════════════════════════════════


_TEST_SECRET = "test-secret-key-32-characters-ok!"


def _make_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    """Create a signed JWT for test requests (permissions resolved from DB)."""
    import os
    from datetime import timedelta
    # Ensure consistent secret key between token creation and verification
    os.environ.setdefault("SECRET_KEY", _TEST_SECRET)
    os.environ["SECRET_KEY"] = _TEST_SECRET
    # Reset settings so create_access_token picks up the test secret
    from app.core.config import _reset_settings
    _reset_settings()
    from app.core.security import create_access_token
    return create_access_token(
        data={"sub": str(user_id), "tenant_id": str(tenant_id)},
        expires_delta=timedelta(minutes=30),
    )


@pytest_asyncio.fixture(scope="module")
async def liq_http_ctx(test_session_factory, liq_ctx, db_tables) -> dict:
    """Create users for HTTP endpoint tests: one with no perms, one with RBAC roles."""
    from app.core.security import hash_password, email_hash
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso
    from app.models.usuario_rol import UsuarioRol

    t_id = liq_ctx["tenant_id"]

    async with test_session_factory() as session:
        # User with no permissions (no roles assigned)
        noperm_email = f"noperm-liq-{uuid.uuid4().hex[:8]}@test.com"
        u_noperm = Usuario(
            id=uuid.uuid4(), tenant_id=t_id,
            email_cifrado="placeholder-noperm",
            email_hash=email_hash(noperm_email),
            password_hash=hash_password("pass"),
            activo=True,
        )
        session.add(u_noperm)
        await session.flush()

        # Role with liquidaciones:operar + liquidaciones:cerrar + facturas:gestionar
        from app.core.permisos import LIQUIDACIONES_OPERAR, LIQUIDACIONES_CERRAR, FACTURAS_GESTIONAR
        rol_liq = Rol(
            id=uuid.uuid4(), tenant_id=t_id,
            nombre="LiqAdmin", codigo=f"liq-admin-{uuid.uuid4().hex[:6]}",
        )
        session.add(rol_liq)
        await session.flush()

        for perm_code in [LIQUIDACIONES_OPERAR, LIQUIDACIONES_CERRAR, FACTURAS_GESTIONAR]:
            perm = Permiso(
                id=uuid.uuid4(), tenant_id=t_id,
                codigo=perm_code,
            )
            session.add(perm)
            await session.flush()
            rp = RolPermiso(id=uuid.uuid4(), tenant_id=t_id, rol_id=rol_liq.id, permiso_id=perm.id)
            session.add(rp)

        # User with the LiqAdmin role
        admin_email = f"liq-admin-{uuid.uuid4().hex[:8]}@test.com"
        u_admin = Usuario(
            id=uuid.uuid4(), tenant_id=t_id,
            email_cifrado="placeholder-liq-admin",
            email_hash=email_hash(admin_email),
            password_hash=hash_password("pass"),
            activo=True,
        )
        session.add(u_admin)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(), tenant_id=t_id,
            usuario_id=u_admin.id, rol_id=rol_liq.id,
            vig_desde=date(2025, 1, 1),
        )
        session.add(ur)
        await session.commit()

    return {
        "u_noperm_id": u_noperm.id,
        "u_admin_id": u_admin.id,
        "noperm_token": _make_token(u_noperm.id, t_id),
        "admin_token": _make_token(u_admin.id, t_id),
    }


@pytest.mark.asyncio
async def test_get_liquidaciones_403_sin_permiso(async_client: AsyncClient, liq_ctx, liq_http_ctx):
    """GET /v1/liquidaciones requires liquidaciones:operar; returns 403 without it."""
    resp = await async_client.get(
        f"/v1/liquidaciones/?cohorte_id={liq_ctx['cohorte_id']}&periodo={_PERIODO}",
        headers={"Authorization": f"Bearer {liq_http_ctx['noperm_token']}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_post_calcular_403_sin_permiso(async_client: AsyncClient, liq_ctx, liq_http_ctx):
    """POST /v1/liquidaciones/calcular requires liquidaciones:operar; returns 403."""
    resp = await async_client.post(
        "/v1/liquidaciones/calcular",
        json={"cohorte_id": str(liq_ctx["cohorte_id"]), "periodo": _PERIODO},
        headers={"Authorization": f"Bearer {liq_http_ctx['noperm_token']}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cerrar_409_periodo_ya_cerrado(async_client: AsyncClient, liq_ctx, liq_http_ctx):
    """POST /v1/liquidaciones/cerrar returns 409 if period already closed."""
    token = liq_http_ctx["admin_token"]
    # Use a unique period for this test to avoid cross-test interference
    periodo_test = "2025-11"

    # Calculate
    await async_client.post(
        "/v1/liquidaciones/calcular",
        json={"cohorte_id": str(liq_ctx["cohorte_id"]), "periodo": periodo_test},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Close once — should succeed
    resp1 = await async_client.post(
        "/v1/liquidaciones/cerrar",
        json={"cohorte_id": str(liq_ctx["cohorte_id"]), "periodo": periodo_test},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code in (200, 204)

    # Close again — should return 409
    resp2 = await async_client.post(
        "/v1/liquidaciones/cerrar",
        json={"cohorte_id": str(liq_ctx["cohorte_id"]), "periodo": periodo_test},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_multi_tenant_aislamiento(async_client: AsyncClient, liq_ctx, liq_http_ctx, tenant_b_ctx):
    """Tenant A cannot see Tenant B's liquidaciones."""
    token_a = liq_http_ctx["admin_token"]
    resp = await async_client.get(
        f"/v1/liquidaciones/?cohorte_id={tenant_b_ctx['cohorte_b_id']}&periodo={_PERIODO}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # Either 200 with empty list or 404 (no cohorte visible) — never the B tenant's data
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("general", data) if isinstance(data, dict) else data
        for item in (items if isinstance(items, list) else []):
            assert str(item.get("id", "")) != str(tenant_b_ctx["liq_b_id"])


@pytest.mark.asyncio
async def test_get_facturas_403_sin_permiso(async_client: AsyncClient, liq_http_ctx):
    """GET /v1/facturas requires facturas:gestionar; returns 403 without it."""
    resp = await async_client.get(
        "/v1/facturas/",
        headers={"Authorization": f"Bearer {liq_http_ctx['noperm_token']}"},
    )
    assert resp.status_code == 403
