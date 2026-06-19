"""Seed test messages for inbox testing."""

import asyncio, os, sys, uuid
from datetime import datetime

sys.path.insert(0, "/app")

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

DB = os.environ.get("DATABASE_URL",
                    "postgresql+asyncpg://activia:changeme@postgres:5432/activia_trace")

# Known user UUIDs from seed_dev.py
UA  = uuid.UUID("00000000-0000-0000-0000-000000000100")  # Admin Sistema
UC  = uuid.UUID("00000000-0000-0000-0000-000000000101")  # Carmen Coordinadora
UP  = uuid.UUID("00000000-0000-0000-0000-000000000102")  # Pablo Profesor
UT  = uuid.UUID("00000000-0000-0000-0000-000000000103")  # Tomás Tutor

T = uuid.UUID("00000000-0000-0000-0000-000000000001")  # tenant


async def seed():
    e = create_async_engine(DB, echo=False)
    try:
        async with e.connect() as c:
            msgs = [
                (UC, UA, "Reunión de coordinación", "Hola, tenemos reunión el viernes a las 10. Saludos, Carmen", False),
                (UP, UA, "Consulta sobre calificaciones", "Admin, necesito que revises las notas de Programación I. Quedan algunos alumnos sin calificación.", False),
                (UT, UA, "Alumnos atrasados", "Te paso el listado de alumnos que tienen actividades pendientes. Son 3 en total.", False),
                (UA, UC, "Confirmación reunión", "Confirmada la reunión del viernes. Nos vamos a conectar por Meet.", False),
                (UA, UP, "Re: Consulta sobre calificaciones", "Ya revisé las notas, todo en orden. Gracias por avisar.", True),
                (UC, UP, "Programa de la materia", "Pablo, necesito que subas el programa actualizado de Programación I.", False),
            ]

            now = datetime.utcnow()
            for remitente, destinatario, asunto, cuerpo, leido in msgs:
                mid = uuid.uuid4()
                await c.execute(
                    sa.text("""
                        INSERT INTO mensajes_internos (id, tenant_id, remitente_id, destinatario_id, asunto, cuerpo, leido, created_at, updated_at)
                        VALUES (:id, :tid, :rem, :dest, :asunto, :cuerpo, :leido, :now, :now)
                        ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": mid,
                        "tid": T,
                        "rem": remitente,
                        "dest": destinatario,
                        "asunto": asunto,
                        "cuerpo": cuerpo,
                        "leido": leido,
                        "now": now,
                    },
                )

            await c.commit()
            print(f"Created {len(msgs)} messages")
    finally:
        await e.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
