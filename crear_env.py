import os

open('backend/.env', 'w').write(
    'DATABASE_URL=postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace\n'
    'DATABASE_URL_TEST=postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test\n'
    'SECRET_KEY=dev-secret-key-activia-trace-2026-local\n'
    'ENCRYPTION_KEY=0000000000000000000000000000000000000000000000000000000000000001\n'
    'CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]\n'
)
print('backend/.env creado.')

os.makedirs('frontend', exist_ok=True)
open('frontend/.env.local', 'w').write(
    'VITE_API_BASE_URL=http://localhost:8000\n'
    'VITE_TENANT_ID=00000000-0000-0000-0000-000000000001\n'
)
print('frontend/.env.local creado.')
