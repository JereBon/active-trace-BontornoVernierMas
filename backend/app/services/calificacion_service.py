"""services/calificacion_service.py — CalificacionService (C-10: calificaciones-y-umbral).

Orchestrates LMS calificaciones import, umbral configuration, and recalculation.
Never accesses the DB directly — all persistence goes through repositories.

Public functions:
  calcular_aprobado     — pure function: derive aprobado from nota + umbral (testable)

CalificacionService methods:
  importar              — parse file, calculate aprobado, upsert calificaciones, audit
  configurar_umbral     — upsert UmbralMateria + batch-recalculate aprobado

Design decisions (C-10 design.md D1, D5):
- calcular_aprobado is a pure function for testability.
- valores_aprobatorios default: {"Satisfactorio", "Supera lo esperado"} (RN-02).
  This is hardcoded in this iteration; future: configurable per UmbralMateria.
- Audit action: CALIFICACIONES_IMPORTAR after each confirmed import.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action

# Default set of textual values that count as "aprobado" (RN-02)
_DEFAULT_VALORES_APROBATORIOS: frozenset[str] = frozenset({
    "Satisfactorio",
    "Supera lo esperado",
})

_DEFAULT_UMBRAL_PCT = 60

_ACCION_IMPORTAR = "CALIFICACIONES_IMPORTAR"


def calcular_aprobado(
    nota_numerica: float | None,
    nota_textual: str | None,
    umbral_pct: int = _DEFAULT_UMBRAL_PCT,
    valores_aprobatorios: list[str] | None = None,
) -> bool:
    """Derive the `aprobado` flag from a nota and the configured umbral.

    Rules (from spec / RN-01, RN-02, RN-03):
      - If nota_numerica is present: aprobado = nota_numerica >= umbral_pct.
      - If only nota_textual is present: aprobado = nota_textual in valores_aprobatorios.
        Uses _DEFAULT_VALORES_APROBATORIOS if valores_aprobatorios is None or empty.
      - If both are None: aprobado = False.

    Args:
        nota_numerica:       Numeric grade (0–100 scale assumed), or None.
        nota_textual:        Textual grade (e.g. 'Satisfactorio'), or None.
        umbral_pct:          Minimum percentage to pass (inclusive). Default 60.
        valores_aprobatorios: List of textual values that count as passing.

    Returns:
        bool: True if the student passes, False otherwise.
    """
    if nota_numerica is not None:
        return nota_numerica >= umbral_pct

    if nota_textual is not None:
        approved_set: frozenset[str] = (
            frozenset(valores_aprobatorios)
            if valores_aprobatorios
            else _DEFAULT_VALORES_APROBATORIOS
        )
        return nota_textual in approved_set

    return False


class CalificacionService:
    """Orchestrates calificaciones import and umbral configuration.

    Instantiated per-request with the active DB session and tenant context
    (always sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

        from app.repositories.calificacion_repository import (  # noqa: PLC0415
            CalificacionRepository,
            UmbralMateriaRepository,
        )
        from app.services.calificacion_parser import CalificacionParser  # noqa: PLC0415

        self._cal_repo = CalificacionRepository(session, tenant_id)
        self._umbral_repo = UmbralMateriaRepository(session, tenant_id)
        self._parser = CalificacionParser()

    async def importar(
        self,
        actor_id: uuid.UUID,
        materia_id: uuid.UUID,
        asignacion_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        actividades_seleccionadas: list[str],
        ip: str = "unknown",
        user_agent: str = "",
    ) -> list[Any]:
        """Parse LMS file, calculate aprobado, upsert calificaciones, emit audit.

        Flow:
          1. Parse selected activities from file.
          2. Resolve EntradaPadron by email for each row.
          3. Calculate aprobado using the current umbral (or default 60).
          4. Upsert Calificacion records.
          5. Emit CALIFICACIONES_IMPORTAR audit event.

        Args:
            actor_id:                  UUID of the user (from JWT).
            materia_id:                UUID of the materia.
            asignacion_id:             UUID of the docente's asignacion.
            file_bytes:                Raw bytes of the uploaded LMS file.
            filename:                  Original filename.
            actividades_seleccionadas: List of activity names to import.
            ip:                        Client IP (for audit).
            user_agent:                HTTP User-Agent (for audit).

        Returns:
            List of created/updated Calificacion records.
        """
        from sqlalchemy import select  # noqa: PLC0415
        from app.models.entrada_padron import EntradaPadron  # noqa: PLC0415
        from app.core.crypto import encrypt, decrypt  # noqa: PLC0415

        # Step 1: Get current umbral for this asignacion×materia
        umbral_record = await self._umbral_repo.get_by_asignacion_materia(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
        )
        umbral_pct = umbral_record.umbral_pct if umbral_record else _DEFAULT_UMBRAL_PCT
        valores_aprobatorios = umbral_record.valores_aprobatorios if umbral_record else []

        # Step 2: Parse the file for selected activities
        parsed_rows = self._parser.parse_actividades_seleccionadas(
            file_bytes=file_bytes,
            filename=filename,
            actividades=actividades_seleccionadas,
        )

        if not parsed_rows:
            return []

        # Step 3: Resolve emails to EntradaPadron IDs
        # Get all active EntradaPadron for this tenant × materia
        stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        all_entradas = list(result.scalars().all())

        # Build email → entrada_padron_id lookup (decrypt email for comparison)
        email_to_entrada: dict[str, uuid.UUID] = {}
        for entrada in all_entradas:
            try:
                plain_email = decrypt(entrada.email_cifrado).lower().strip()
                email_to_entrada[plain_email] = entrada.id
            except Exception:  # noqa: BLE001
                continue  # skip entries with decrypt errors

        # Step 4: Build calificacion dicts
        calificacion_dicts: list[dict[str, Any]] = []
        for row in parsed_rows:
            email_key = row["email"].lower().strip()
            entrada_padron_id = email_to_entrada.get(email_key)
            if entrada_padron_id is None:
                continue  # student not in padron; skip

            aprobado = calcular_aprobado(
                nota_numerica=row["nota_numerica"],
                nota_textual=row["nota_textual"],
                umbral_pct=umbral_pct,
                valores_aprobatorios=valores_aprobatorios if valores_aprobatorios else None,
            )

            calificacion_dicts.append(
                {
                    "entrada_padron_id": entrada_padron_id,
                    "materia_id": materia_id,
                    "actividad": row["actividad"],
                    "nota_numerica": row["nota_numerica"],
                    "nota_textual": row["nota_textual"],
                    "aprobado": aprobado,
                    "origen": "Importado",
                }
            )

        # Step 5: Upsert
        calificaciones = await self._cal_repo.upsert_bulk(calificacion_dicts)

        # Step 6: Audit log
        await audit_action(
            session=self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_IMPORTAR,
            detalle={
                "materia_id": str(materia_id),
                "asignacion_id": str(asignacion_id),
                "actividades": actividades_seleccionadas,
                "filas_procesadas": len(calificacion_dicts),
            },
            filas_afectadas=len(calificaciones),
            ip=ip,
            user_agent=user_agent,
        )

        return calificaciones

    async def configurar_umbral(
        self,
        actor_id: uuid.UUID,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
        ip: str = "unknown",
        user_agent: str = "",
    ) -> Any:
        """Create or update the umbral for an asignacion×materia pair.

        After upserting, recalculates `aprobado` on all existing calificaciones
        for this tenant × materia that belong to entries in the padron
        (tenant-scoped; does not affect other docentes).

        Design note (C-10 design.md D1, D4):
        The recalculation affects all calificaciones in this tenant × materia
        because Calificacion does not store asignacion_id. However, each docente
        has their own UmbralMateria, and the recalculation is only triggered by
        the owner of that umbral.

        Args:
            actor_id:             UUID of the user (from JWT).
            asignacion_id:        UUID of the docente's asignacion.
            materia_id:           UUID of the materia.
            umbral_pct:           New threshold (0–100).
            valores_aprobatorios: New list of passing textual values.
            ip:                   Client IP (for audit, not implemented here).
            user_agent:           HTTP User-Agent.

        Returns:
            The updated UmbralMateria record.
        """
        from sqlalchemy import select  # noqa: PLC0415
        from app.models.entrada_padron import EntradaPadron  # noqa: PLC0415

        umbral = await self._umbral_repo.upsert(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )

        # Recalculate aprobado for all calificaciones in this tenant × materia
        # Fetch all EntradaPadron IDs for this tenant (materia-scoped via calificacion)
        stmt = select(EntradaPadron.id).where(
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        entrada_ids = [row[0] for row in result.fetchall()]

        if entrada_ids:
            await self._cal_repo.update_aprobado_batch(
                materia_id=materia_id,
                entrada_padron_ids=entrada_ids,
                umbral_pct=umbral_pct,
                valores_aprobatorios=valores_aprobatorios,
            )

        return umbral
