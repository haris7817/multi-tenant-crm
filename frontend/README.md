# CRM Frontend (React + Vite + TypeScript)

Tenant-aware SPA for the multi-tenant CRM. Talks to the DRF API at the tenant
subdomain (`http://<workspace>.crm.local:8000`).

- **Stack:** React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack
  Query, Axios, Recharts.
- **Auth:** JWT stored in localStorage; the Axios client sets the tenant base
  URL + `Authorization` header per request and refreshes on 401.

## Run (Docker — recommended)

The frontend runs as a Compose service (installs deps on first start):

```bash
docker compose up -d frontend
```

Open **http://localhost:5173** and sign in:
- **Workspace:** `acme` (or `globex`)
- **Email:** `owner@acme.crm.local`  · **Password:** `password123`

> Requires the hosts-file entries so the browser can resolve the tenant API:
> `127.0.0.1  crm.local acme.crm.local globex.crm.local`

## Useful commands

```bash
docker compose run --rm frontend npm install     # install/refresh deps
docker compose run --rm frontend npm run build    # type-check + production build
docker compose run --rm frontend npm run lint      # tsc --noEmit
```

## Structure

```
src/
├── api/         # axios client (tenant-aware) + TanStack Query hooks
├── auth/        # AuthContext, token storage
├── components/  # Layout, modals, forms
├── lib/         # shared TS types (mirror the DRF serializers)
└── pages/       # Login, Dashboard (analytics), Leads, Pipeline
```

## Implemented
- Login (workspace + email + password), protected routes, logout
- Leads: searchable/filterable table, create/edit/delete (role-gated UI)
- Pipeline: kanban board, drag a card between stages to move a deal, create deal
- Dashboard: KPI cards + charts (deals by stage, leads over time)
- Tasks: filter by status/priority, create, toggle done, delete
- Activity: tenant-scoped audit timeline with field diffs, filter by action
- Members: list, invite, change role, remove (Admin+)

## Note on host npm
The host's TLS can't reach the npm registry (corporate cert-revocation block),
so deps are installed **inside the container**. Run npm via
`docker compose run --rm frontend ...` rather than on the host.
