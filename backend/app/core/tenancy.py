"""core/tenancy.py — RESERVADO para C-02 (resolución y aislamiento de tenant).

This module will implement:
  - Tenant resolution from JWT claims
  - Row-level tenancy enforcement (tenant_id filter on all queries)
  - Tenant context propagation

Multi-tenancy rule (non-negotiable):
  - tenant_id on every table
  - Repositories filter by tenant_id by default
  - A query without tenant scope is a bug that fails code review

C-01 intentionally leaves this empty.
Do NOT add tenancy logic here until C-02.
"""
