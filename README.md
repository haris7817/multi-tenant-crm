# Multi-Tenant SaaS CRM (Learning Project)

A from-scratch, phased build of a multi-tenant SaaS CRM to learn industry SaaS
concepts: **multi-tenancy, RBAC, audit logs, and background jobs**.

- **Backend:** Django 5 + DRF + JWT
- **Frontend:** React + Vite (added in Phase 7)
- **Infra:** PostgreSQL + Redis + Celery, all via Docker Compose
- **Tenant isolation:** shared schema + `tenant_id`, routed by **subdomain**
  (e.g. `acme.crm.local`)

See [the build plan](../../.claude/plans/lets-plan-i-have-zany-boole.md) for the
full phase-by-phase roadmap.

## Quick start

```bash
cp .env.example .env            # adjust if you like
docker compose up --build       # starts db, redis, web
```

- API health check: http://localhost:8000/api/health/
- Swagger UI: http://localhost:8000/api/docs/

## Running tests

```bash
docker compose run --rm web pytest
```

## Local subdomains (Phase 1+)

Tenants are addressed by subdomain. For local dev, map a few to `127.0.0.1` in
your hosts file (`C:\Windows\System32\drivers\etc\hosts` on Windows):

```
127.0.0.1   crm.local acme.crm.local globex.crm.local
```

## Phase status

- [x] **Phase 0** — Foundation & infra (Django, DRF, Swagger, Docker, smoke test)
- [x] **Phase 1** — Multi-tenancy core (subdomain middleware, `TenantManager`, isolation tests)
- [x] **Phase 2** — Accounts, JWT auth & RBAC (custom User, Membership/Role, tenant-bound tokens)
- [ ] **Phase 3** — Core CRM (leads, deals, tasks)
- [ ] **Phase 4** — Activity / audit logs
- [ ] **Phase 5** — Celery background jobs & email
- [ ] **Phase 6** — Analytics dashboard
- [ ] **Phase 7** — React + Vite frontend
```
