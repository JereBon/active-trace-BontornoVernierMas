"""seed_dev.py — Datos de prueba para desarrollo.

    docker-compose exec api python scripts/seed_dev.py
"""

import asyncio, os, sys, uuid
from datetime import date, datetime, timezone

sys.path.insert(0, "/app")

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

DB = os.environ.get("DATABASE_URL",
                    "postgresql+asyncpg://activia:changeme@postgres:5432/activia_trace")

T   = uuid.UUID("00000000-0000-0000-0000-000000000001")   # tenant
CAR = uuid.UUID("00000000-0000-0000-0000-000000000010")   # carrera
C24 = uuid.UUID("00000000-0000-0000-0000-000000000020")   # cohorte 2024
C25 = uuid.UUID("00000000-0000-0000-0000-000000000021")   # cohorte 2025
MP  = uuid.UUID("00000000-0000-0000-0000-000000000030")   # materia Prog I
MB  = uuid.UUID("00000000-0000-0000-0000-000000000031")   # materia BD
UA  = uuid.UUID("00000000-0000-0000-0000-000000000100")   # admin
UC  = uuid.UUID("00000000-0000-0000-0000-000000000101")   # coord
UP  = uuid.UUID("00000000-0000-0000-0000-000000000102")   # profesor
UT  = uuid.UUID("00000000-0000-0000-0000-000000000103")   # tutor

NOW = datetime.now(timezone.utc)

ROLES_DEF = [
    ("ALUMNO",      "Alumno"),
    ("TUTOR",       "Tutor"),
    ("PROFESOR",    "Profesor"),
    ("COORDINADOR", "Coordinador"),
    ("NEXO",        "Nexo"),
    ("ADMIN",       "Administrador"),
    ("FINANZAS",    "Finanzas"),
]

PERMISOS_DEF = [
    ("academico:ver_propio",        "Ver propio perfil académico"),
    ("evaluaciones:reservar",       "Reservar evaluaciones"),
    ("avisos:confirmar",            "Confirmar avisos"),
    ("avisos:publicar",             "Publicar avisos"),
    ("calificaciones:importar",     "Importar calificaciones"),
    ("calificaciones:umbral",       "Configurar umbral"),
    ("atrasados:ver",               "Ver análisis de atrasados"),
    ("entregas:ver_sin_corregir",   "Ver entregas sin corregir"),
    ("comunicacion:enviar",         "Enviar comunicaciones"),
    ("comunicacion:aprobar",        "Aprobar comunicaciones"),
    ("encuentros:gestionar",        "Gestionar encuentros"),
    ("guardias:registrar",          "Registrar guardias"),
    ("tareas:gestionar",            "Gestionar tareas internas"),
    ("equipos:asignar",             "Gestionar asignaciones"),
    ("estructura:gestionar",        "Gestionar estructura académica"),
    ("usuarios:gestionar",          "Gestionar usuarios"),
    ("auditoria:ver",               "Ver log de auditoría"),
    ("liquidaciones:operar",        "Operar liquidaciones"),
    ("liquidaciones:cerrar",        "Cerrar liquidaciones"),
    ("facturas:gestionar",          "Gestionar facturas"),
    ("tenant:configurar",           "Configurar tenant"),
    ("impersonacion:usar",          "Usar impersonación"),
    ("padron:leer",                 "Ver padrón"),
    ("padron:cargar",               "Importar padrón"),
    ("padron:vaciar",               "Vaciar padrón"),
]


def nid():
    return uuid.uuid4()


async def seed(eng):
    from argon2 import PasswordHasher
    from app.core.crypto import encrypt
    from app.core.security import email_hash as ehash

    pwd = PasswordHasher().hash("Demo1234!")

    async with eng.begin() as c:

        # 1. Tenant
        print("→ Tenant...")
        await c.execute(sa.text("""
            INSERT INTO tenants (id,slug,nombre,activo,comunicacion_requiere_aprobacion,created_at,updated_at)
            VALUES (:id,:slug,:nombre,true,true,:n,:n) ON CONFLICT(id) DO NOTHING
        """), dict(id=T, slug="demo", nombre="Universidad Demo", n=NOW))

        # 2. Roles del tenant
        print("→ Roles...")
        role_ids = {}
        for codigo, nombre in ROLES_DEF:
            rid = nid()
            await c.execute(sa.text("""
                INSERT INTO roles (id,tenant_id,codigo,nombre,created_at,updated_at)
                VALUES (:id,:tid,:codigo,:nombre,:n,:n)
                ON CONFLICT(tenant_id,codigo) DO NOTHING
            """), dict(id=rid, tid=T, codigo=codigo, nombre=nombre, n=NOW))
            row = (await c.execute(sa.text(
                "SELECT id FROM roles WHERE tenant_id=:tid AND codigo=:c"
            ), dict(tid=T, c=codigo))).fetchone()
            if row:
                role_ids[codigo] = row[0]

        # 3. Permisos del tenant
        print("→ Permisos...")
        perm_ids = {}
        for codigo, desc in PERMISOS_DEF:
            pid = nid()
            await c.execute(sa.text("""
                INSERT INTO permisos (id,tenant_id,codigo,descripcion,created_at,updated_at)
                VALUES (:id,:tid,:codigo,:desc,:n,:n)
                ON CONFLICT(tenant_id,codigo) DO NOTHING
            """), dict(id=pid, tid=T, codigo=codigo, desc=desc, n=NOW))
            row = (await c.execute(sa.text(
                "SELECT id FROM permisos WHERE tenant_id=:tid AND codigo=:c"
            ), dict(tid=T, c=codigo))).fetchone()
            if row:
                perm_ids[codigo] = row[0]

        # 4. Asignar permisos a roles
        print("→ Rol-permisos...")
        rol_perm_map = {
            "ADMIN":      list(perm_ids.keys()),
            "COORDINADOR": [
                "estructura:gestionar","usuarios:gestionar",
                "padron:leer","padron:cargar","padron:vaciar",
                "calificaciones:importar","calificaciones:umbral",
                "atrasados:ver","entregas:ver_sin_corregir",
                "comunicacion:enviar","comunicacion:aprobar",
                "equipos:asignar","encuentros:gestionar","guardias:registrar",
                "avisos:publicar","avisos:confirmar","auditoria:ver",
            ],
            "PROFESOR": [
                "estructura:gestionar","padron:leer","padron:cargar",
                "calificaciones:importar","calificaciones:umbral",
                "atrasados:ver","entregas:ver_sin_corregir",
                "comunicacion:enviar","equipos:asignar",
                "encuentros:gestionar","guardias:registrar",
                "avisos:publicar","avisos:confirmar",
            ],
            "TUTOR": [
                "padron:leer","atrasados:ver",
                "encuentros:gestionar","guardias:registrar",
                "avisos:confirmar","academico:ver_propio",
            ],
            "ALUMNO":   ["academico:ver_propio","avisos:confirmar","evaluaciones:reservar"],
            "NEXO":     ["estructura:gestionar","usuarios:gestionar"],
            "FINANZAS": ["auditoria:ver","liquidaciones:operar","liquidaciones:cerrar","facturas:gestionar"],
        }
        for rol_codigo, perms in rol_perm_map.items():
            rid = role_ids.get(rol_codigo)
            if not rid:
                continue
            for pc in perms:
                pid = perm_ids.get(pc)
                if pid:
                    await c.execute(sa.text("""
                        INSERT INTO rol_permisos (id,tenant_id,rol_id,permiso_id,created_at)
                        VALUES (:id,:tid,:r,:p,:n)
                        ON CONFLICT(rol_id,permiso_id) DO NOTHING
                    """), dict(id=nid(), tid=T, r=rid, p=pid, n=NOW))

        # 5. Usuarios
        print("→ Usuarios...")
        users = [
            (UA, "Admin",  "Sistema",      "admin@demo.edu",       "ADMIN"),
            (UC, "Carmen", "Coordinadora", "coordinador@demo.edu", "COORDINADOR"),
            (UP, "Pablo",  "Profesor",     "profesor@demo.edu",    "PROFESOR"),
            (UT, "Tomás",  "Tutor",        "tutor@demo.edu",       "TUTOR"),
        ]
        for uid_, nombre, apellidos, email, rol_c in users:
            await c.execute(sa.text("""
                INSERT INTO usuarios (id,tenant_id,nombre,apellidos,
                    email_cifrado,email_hash,password_hash,totp_activo,activo,created_at,updated_at)
                VALUES (:id,:tid,:nombre,:apellidos,:ec,:eh,:pwd,false,true,:n,:n)
                ON CONFLICT(id) DO NOTHING
            """), dict(id=uid_, tid=T, nombre=nombre, apellidos=apellidos,
                       ec=encrypt(email), eh=ehash(email), pwd=pwd, n=NOW))
            rid = role_ids.get(rol_c)
            if rid:
                await c.execute(sa.text("""
                    INSERT INTO usuario_roles (id,tenant_id,usuario_id,rol_id,vig_desde,created_at,updated_at)
                    VALUES (:id,:tid,:uid,:rid,:vd,:n,:n)
                    ON CONFLICT(usuario_id,rol_id,vig_desde) DO NOTHING
                """), dict(id=nid(), tid=T, uid=uid_, rid=rid,
                           vd=date(2025,3,1), n=NOW))

        # 6. Estructura académica
        print("→ Estructura académica...")
        await c.execute(sa.text("""
            INSERT INTO carreras (id,tenant_id,codigo,nombre,created_at,updated_at)
            VALUES (:id,:tid,'IS','Ingeniería en Sistemas',:n,:n)
            ON CONFLICT(id) DO NOTHING
        """), dict(id=CAR, tid=T, n=NOW))

        for cid, nombre, anio in [(C24,"Cohorte 2024",2024),(C25,"Cohorte 2025",2025)]:
            await c.execute(sa.text("""
                INSERT INTO cohortes (id,tenant_id,carrera_id,nombre,anio,vig_desde,created_at,updated_at)
                VALUES (:id,:tid,:cid,:nombre,:anio,:vd,:n,:n)
                ON CONFLICT(id) DO NOTHING
            """), dict(id=cid, tid=T, cid=CAR, nombre=nombre, anio=anio,
                       vd=date(anio,3,1), n=NOW))

        for mid, nombre, codigo in [
            (MP,"Programación I","PROG1"),
            (MB,"Bases de Datos","BD1"),
        ]:
            await c.execute(sa.text("""
                INSERT INTO materias (id,tenant_id,nombre,codigo,created_at,updated_at)
                VALUES (:id,:tid,:nombre,:codigo,:n,:n)
                ON CONFLICT(id) DO NOTHING
            """), dict(id=mid, tid=T, nombre=nombre, codigo=codigo, n=NOW))

        # 7. Asignaciones docentes
        print("→ Asignaciones...")
        for uid_, mid, cid, rol in [
            (UP, MP, C25, "PROFESOR"),
            (UT, MP, C25, "TUTOR"),
            (UC, MB, C25, "COORDINADOR"),
        ]:
            await c.execute(sa.text("""
                INSERT INTO asignaciones
                  (id,tenant_id,usuario_id,rol,materia_id,carrera_id,cohorte_id,comisiones,desde,created_at,updated_at)
                VALUES (:id,:tid,:uid,:rol,:mid,:car,:cid,'{}' ,:desde,:n,:n)
                ON CONFLICT(id) DO NOTHING
            """), dict(id=nid(), tid=T, uid=uid_, rol=rol,
                       mid=mid, car=CAR, cid=cid,
                       desde=date(2025,3,1), n=NOW))

    print("\n✅ Seed completo!\n")
    print("=" * 57)
    print("  Swagger:  http://localhost:8000/docs")
    print("  ROL           EMAIL                    PASSWORD")
    print("  -----------   -----------------------  ----------")
    print("  ADMIN         admin@demo.edu           Demo1234!")
    print("  COORDINADOR   coordinador@demo.edu     Demo1234!")
    print("  PROFESOR      profesor@demo.edu        Demo1234!")
    print("  TUTOR         tutor@demo.edu           Demo1234!")
    print("")
    print("  Tenant:  Universidad Demo  (slug: demo)")
    print("  Carrera: Ingeniería en Sistemas (IS)")
    print("  Materias: Programación I / Bases de Datos")
    print("  Cohortes: 2024 / 2025")
    print("=" * 57)


async def main():
    e = create_async_engine(DB, echo=False)
    try:
        await seed(e)
    finally:
        await e.dispose()


if __name__ == "__main__":
    asyncio.run(main())
