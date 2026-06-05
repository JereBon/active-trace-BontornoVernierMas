"""tests/test_equipos_schemas.py — Unit tests for C-08 Asignacion schemas.

TDD cycles (1.2):
  - Invalid rol → ValidationError
  - Empty usuario_ids in masiva → ValidationError
  - Extra fields → ValidationError (extra='forbid')
  - origen == destino in ClonarEquipoRequest → ValidationError
  - Valid payloads → pass
"""

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.asignacion import (
    AsignacionCreate,
    AsignacionMasivaCreate,
    AsignacionUpdate,
    ClonarEquipoRequest,
    VigenciaMasivaRequest,
)

_TODAY = date.today()
_UUID = uuid.uuid4()
_UUID2 = uuid.uuid4()


# ── AsignacionCreate ──────────────────────────────────────────────────────────


def test_asignacion_create_valid():
    obj = AsignacionCreate(usuario_id=_UUID, rol="PROFESOR", desde=_TODAY)
    assert obj.rol == "PROFESOR"


def test_asignacion_create_invalid_rol():
    with pytest.raises(ValidationError, match="rol must be one of"):
        AsignacionCreate(usuario_id=_UUID, rol="SUPERADMIN", desde=_TODAY)


def test_asignacion_create_extra_field_forbidden():
    with pytest.raises(ValidationError):
        AsignacionCreate(usuario_id=_UUID, rol="TUTOR", desde=_TODAY, unknown_field="x")


def test_asignacion_create_all_roles_valid():
    for rol in ["ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"]:
        obj = AsignacionCreate(usuario_id=_UUID, rol=rol, desde=_TODAY)
        assert obj.rol == rol


# ── AsignacionUpdate ──────────────────────────────────────────────────────────


def test_asignacion_update_all_optional():
    obj = AsignacionUpdate()
    assert obj.rol is None
    assert obj.desde is None


def test_asignacion_update_invalid_rol():
    with pytest.raises(ValidationError, match="rol must be one of"):
        AsignacionUpdate(rol="BADROL")


def test_asignacion_update_extra_field_forbidden():
    with pytest.raises(ValidationError):
        AsignacionUpdate(rol="TUTOR", bogus="x")


# ── AsignacionMasivaCreate ────────────────────────────────────────────────────


def test_asignacion_masiva_empty_list_rejected():
    with pytest.raises(ValidationError):
        AsignacionMasivaCreate(usuario_ids=[], rol="TUTOR", desde=_TODAY)


def test_asignacion_masiva_valid():
    obj = AsignacionMasivaCreate(usuario_ids=[_UUID, _UUID2], rol="TUTOR", desde=_TODAY)
    assert len(obj.usuario_ids) == 2


def test_asignacion_masiva_invalid_rol():
    with pytest.raises(ValidationError, match="rol must be one of"):
        AsignacionMasivaCreate(usuario_ids=[_UUID], rol="GHOST", desde=_TODAY)


def test_asignacion_masiva_extra_field_forbidden():
    with pytest.raises(ValidationError):
        AsignacionMasivaCreate(usuario_ids=[_UUID], rol="TUTOR", desde=_TODAY, x=1)


# ── ClonarEquipoRequest ───────────────────────────────────────────────────────


def test_clonar_equipo_valid():
    obj = ClonarEquipoRequest(
        materia_id=_UUID,
        carrera_id=_UUID2,
        origen_cohorte_id=uuid.uuid4(),
        destino_cohorte_id=uuid.uuid4(),
        desde=_TODAY,
    )
    assert obj.materia_id == _UUID


def test_clonar_equipo_origen_igual_destino_rejected():
    cid = uuid.uuid4()
    with pytest.raises(ValidationError, match="origen_cohorte_id and destino_cohorte_id must be different"):
        ClonarEquipoRequest(
            materia_id=_UUID,
            carrera_id=_UUID2,
            origen_cohorte_id=cid,
            destino_cohorte_id=cid,
            desde=_TODAY,
        )


def test_clonar_equipo_extra_field_forbidden():
    with pytest.raises(ValidationError):
        ClonarEquipoRequest(
            materia_id=_UUID,
            carrera_id=_UUID2,
            origen_cohorte_id=uuid.uuid4(),
            destino_cohorte_id=uuid.uuid4(),
            desde=_TODAY,
            extra_key="x",
        )


# ── VigenciaMasivaRequest ─────────────────────────────────────────────────────


def test_vigencia_masiva_valid():
    obj = VigenciaMasivaRequest(materia_id=_UUID, carrera_id=_UUID2, cohorte_id=uuid.uuid4(), desde=_TODAY)
    assert obj.hasta is None


def test_vigencia_masiva_extra_field_forbidden():
    with pytest.raises(ValidationError):
        VigenciaMasivaRequest(
            materia_id=_UUID,
            carrera_id=_UUID2,
            cohorte_id=uuid.uuid4(),
            desde=_TODAY,
            nope=True,
        )
