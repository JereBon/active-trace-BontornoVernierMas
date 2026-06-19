"""Seed script: Create Maria García as PROFESOR"""
import asyncio, sys, uuid
sys.path.insert(0, '/app')
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, text
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.core.crypto import encrypt
from app.core.security import email_hash as compute_email_hash, hash_password

ENGINE_URL = "postgresql+asyncpg://trace:trace@db:5432/trace"
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

async def main():
    engine = create_async_engine(ENGINE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(select(Rol).where(Rol.codigo == "PROFESOR"))
        row = result.fetchone()
        if not row:
            print("ERROR: PROFESOR role not found. Run migrations first.")
            return
        rol_id = row[0]
        print(f"PROFESOR role id: {rol_id}")

        email_hash = compute_email_hash("maria@demo.edu")
        existing = await conn.execute(
            text("SELECT id FROM usuarios WHERE email_hash = :h"),
            {"h": email_hash},
        )
        if existing.fetchone():
            print("User maria@demo.edu already exists. Skipping.")
            return

        data = {
            "email_cifrado": encrypt("maria@demo.edu"),
            "email_hash": email_hash,
            "password_hash": hash_password("Demo1234!"),
            "nombre": "María",
            "apellidos": "García",
            "dni_cifrado": encrypt("30123456"),
            "cuil_cifrado": encrypt("27-30123456-8"),
            "activo": True,
            "tenant_id": TENANT_ID,
        }

        ins = Usuario.__table__.insert().values(**data)
        result = await conn.execute(ins)
        uid = result.inserted_primary_key[0]
        print(f"Created user: {uid}")

        ins2 = UsuarioRol.__table__.insert().values(
            usuario_id=uid,
            rol_id=rol_id,
            vig_desde=date.today(),
            tenant_id=TENANT_ID,
        )
        await conn.execute(ins2)
        await conn.commit()
        print("Role PROFESOR assigned.")
        print("Login: maria@demo.edu / Demo1234!")

asyncio.run(main())
