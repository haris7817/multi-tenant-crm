# Multi-Tenant SaaS CRM — Master Roadmap

The full plan: what we've built, and what's next. Future phases are ordered
**features & integrations first, production deployment last** (so the app keeps
growing in capability before we lock it down for release).

**Legend:** ✅ done · 🔭 planned · (each phase breaks into sub-phases)

**Stack:** Django 5 · DRF · PostgreSQL · Redis · Celery · Docker · React + Vite +
TypeScript (Tailwind, TanStack Query). Multi-tenancy = **shared schema +
`tenant_id`**, routed by **subdomain**.

---

# Part I — Completed (Phases 0–7)

## ✅ Phase 0 — Foundation & Infrastructure
- 0.1 Django project + DRF + drf-spectacular (Swagger at `/api/docs/`)
- 0.2 Docker Compose: Postgres + Redis + web
- 0.3 Settings split: `base` / `dev` / `test`; env-driven config
- 0.4 Health check endpoint + smoke tests

## ✅ Phase 1 — Multi-Tenancy Core ⭐
- 1.1 `Tenant` + `Domain` models
- 1.2 Thread-local "current tenant" context
- 1.3 `TenantManager` (auto-scopes queries) + `TenantBaseModel`
- 1.4 `TenantMiddleware` (resolves tenant from subdomain)
- 1.5 `seed_tenants` management command (demo data)
- 1.6 Isolation tests (Tenant A cannot see Tenant B)

## ✅ Phase 2 — Accounts, JWT Auth & RBAC
- 2.1 Custom email `User`; `Membership` + `Role` (Owner→Viewer) with `ROLE_LEVEL`
- 2.2 Tenant-bound JWT (claims: `tenant_id`, `role`); login / refresh / me
- 2.3 Permission classes: `IsTenantMember`, `HasTenantRole`
- 2.4 Member management API (invite / list / change role / remove)
- 2.5 Public workspace registration (creates tenant + owner + pipeline)

## ✅ Phase 3 — Core CRM
- 3.1 `Lead`, `Stage` (pipeline), `Deal`, `Task` models
- 3.2 Shared `TenantModelViewSet` (per-request scoping, role gating, owner stamping)
- 3.3 Pipeline endpoints: kanban board + move-deal-to-stage
- 3.4 Filtering, search, ordering

## ✅ Phase 4 — Activity / Audit Logs
- 4.1 `AuditLog` (GenericForeignKey, field-level diff, indexes)
- 4.2 Auto-recording baked into the base viewset (create/update/delete)
- 4.3 Read-only tenant-scoped timeline API

## ✅ Phase 5 — Background Jobs & Email (Celery + Redis)
- 5.1 Celery worker + beat services
- 5.2 Async welcome email (register / invite) via `transaction.on_commit`
- 5.3 Async deal-won email
- 5.4 Scheduled `flag_stale_leads` (system-wide, all tenants)

## ✅ Phase 6 — Analytics Dashboard
- 6.1 Aggregate endpoints: summary, deals-by-stage, leads-by-status,
  leads-over-time, revenue-forecast (DB-side aggregation)
- 6.2 Redis-cached summary (tenant-scoped key + TTL)

## ✅ Phase 7 — React + Vite Frontend
- 7.0 Foundation: TS, Tailwind, Router, TanStack Query, tenant-aware Axios, app shell
- 7.1 Auth: login (workspace + email + password), refresh, logout, protected routes
- 7.2 Leads: table, search/filter, create/edit/delete (role-gated)
- 7.3 Pipeline: kanban with drag-to-move, create deal
- 7.4 Dashboard: KPI cards + Recharts
- 7.5 Tasks · 7.6 Activity timeline · 7.7 Members admin
- (Dev: Vite proxy injects tenant `Host` so no hosts-file/CORS needed)

**Tooling:** Postman collection (`/postman`) covering all endpoints.

---

# Part II — Future Phases (8 → 15)

> Ordering principle: grow capability and openness first; **deploy last**.

## ✅ Phase 8 — CRM Feature Depth
Make the core CRM feel real before exposing it.
- 8.1 ✅ **Notes & comments** on leads/deals (GenericFK, audited)
- 8.2 ✅ **File attachments** (model + media storage; local now, S3 later)
- 8.3 ✅ **Full-text search** across leads (Postgres `SearchVector`)
- 8.4 ✅ **CSV import/export** (bulk lead import with validation; export view)
- 8.5 ✅ **Bulk actions** (multi-select: set status/owner, add tag, delete)
- 8.6 ✅ **Saved views / smart filters** (persisted per user)
- 8.7 ✅ **Per-tenant custom fields** (definitions + JSON values)
- 8.8 ✅ **Tags / labels** on records
- (Frontend: tags column, full-text search, bulk bar, import/export, lead
  detail drawer with notes/attachments/tags/custom fields)

## 🔭 Phase 9 — Notifications & Collaboration
- 9.1 **In-app notifications** model + feed + unread counts
- 9.2 **Real-time updates** via Django Channels + WebSockets (live pipeline/notifs)
- 9.3 **Email digests** (daily "your stale leads / tasks due") via Celery beat
- 9.4 **Task reminders** (due-date notifications)
- 9.5 **Assignment notifications** (notify on lead/task assignment)

## 🔭 Phase 10 — Public API Platform
The authenticated surface external apps build against.
- 10.1 **API versioning** (`/api/v1/`) + deprecation policy
- 10.2 **Per-tenant API keys** (model, hashed storage, create/revoke UI)
- 10.3 **Scopes** (read-only vs read-write; resource scopes) + key auth class
- 10.4 **Rate limiting / throttling** per key + per tenant (DRF throttles + Redis)
- 10.5 **Consistent error envelope**, pagination/cursor standards, idempotency keys
- 10.6 **Docs & SDKs**: hosted OpenAPI docs, generated TS/Python clients

## 🔭 Phase 11 — Webhooks (Outbound + Inbound)
The most useful integration primitive.
- 11.1 **Event catalog** (`lead.created`, `deal.won`, `task.completed`, …)
- 11.2 **Transactional outbox** (write event in same txn as the change)
- 11.3 **Outbound delivery** via Celery: **HMAC-signed** payloads, **retries** w/ backoff
- 11.4 **Delivery logs + replay** (per-tenant dashboard, redeliver failed)
- 11.5 **Webhook subscription management** (UI + API: subscribe URLs to events)
- 11.6 **Inbound webhook receivers** (signature-verified endpoints for partners)

## 🔭 Phase 12 — OAuth, SSO & Connection Framework
- 12.1 **Social login / SSO** (Google, Microsoft) via django-allauth
- 12.2 **Be an OAuth2 provider** (django-oauth-toolkit) for third-party apps
- 12.3 **Encrypted per-tenant credential store** (Fernet/field encryption)
- 12.4 **Connection framework**: OAuth connect flows, token refresh, status

## 🔭 Phase 13 — External Connectors (the "connect with other apps" payoff)
Built on 10–12. Each is a sub-phase.
- 13.1 **Stripe billing** — subscriptions per tenant, plans/quotas, metered usage,
  inbound Stripe webhooks, dunning (the SaaS's own monetization)
- 13.2 **Real email provider** — SendGrid/SES/Mailgun outbound + **inbound parse**
  to log replies onto leads
- 13.3 **Slack / Teams** — "deal won → #sales" notifications, slash commands
- 13.4 **Google / Microsoft** — calendar sync for tasks, email sync onto leads
- 13.5 **Zapier / Make app** — expose triggers (new lead) + actions (built on 10+11)
- 13.6 **Lead enrichment** (Clearbit/Apollo) + **telephony** (Twilio SMS/click-to-call)

## 🔭 Phase 14 — AI Assistant / Chatbot
A conversational assistant over each tenant's CRM data.
*(LLM provider/API is TBD — decided at build time; the design stays
provider-agnostic behind an abstraction.)*
- 14.1 **Chat UI** in the SPA — streaming responses, conversation history
- 14.2 **Backend chat endpoint** — streaming (SSE), scoped to the current
  tenant + user; conversation persistence
- 14.3 **Tool / function calling over the CRM API** — the assistant can search
  leads, summarize a deal, create tasks, move deals; **every tool call runs
  through the same RBAC + tenant scoping** as a normal request (a Viewer's
  assistant can't write, no cross-tenant access)
- 14.4 **Retrieval / grounding (RAG)** — semantic search across leads/deals/notes
  (pgvector embeddings), strictly tenant-filtered
- 14.5 **Use cases** — NL search ("stale deals in negotiation > $5k"), record
  summaries, draft follow-up emails, daily briefing
- 14.6 **Guardrails & ops** — tenant isolation in retrieval, permission-aware
  tool execution, prompt-injection defense, **audit-log every AI action**,
  token/cost limits + per-tenant rate caps
- 14.7 **Provider abstraction** — pluggable LLM client so the model/API choice
  stays a config decision

## 🔭 Phase 15 — Observability, Testing & Quality
Pre-flight before going live.
- 15.1 **Error tracking** (Sentry, backend + frontend)
- 15.2 **Structured JSON logging** + request/tenant correlation IDs
- 15.3 **Metrics** (Prometheus/Grafana) + `/healthz` `/readyz`
- 15.4 **Test depth**: factory_boy, more isolation/RBAC/webhook tests, coverage gate
- 15.5 **Frontend tests** (Vitest + Playwright E2E)
- 15.6 **CI** (GitHub Actions: lint, test, build, dependency/security scan)

## 🔭 Phase 16 — Production Hardening & Deployment (FINAL) 🚀
Lock it down and ship it.
- 16.1 **`prod` settings**: `DEBUG=False`, locked `ALLOWED_HOSTS`/CORS, secrets from
  a vault, security headers (HSTS, SSL redirect, secure cookies, CSP)
- 16.2 **App server**: Gunicorn/Uvicorn behind **Nginx/Caddy/Traefik**, HTTPS (Let's Encrypt)
- 16.3 **Static/media**: WhiteNoise or **S3 + CDN**; user uploads to S3
- 16.4 **Database**: managed Postgres, connection pooling (PgBouncer), automated backups
- 16.5 **Celery in prod**: `django-celery-beat` (DB schedule), tuned concurrency,
  Flower monitoring, idempotent + retrying tasks
- 16.6 **Prod containers**: multi-stage Dockerfiles, non-root, healthchecks, small images
- 16.7 **Orchestration & CD**: deploy target (Render/Fly/ECS/Kubernetes),
  zero-downtime releases, migrations-on-deploy, rollback
- 16.8 **Tenant lifecycle & compliance**: suspension, quotas, GDPR export/delete,
  data-retention policies, rate-limit/abuse monitoring

---

## Recommended sequencing
- **Fastest "feels like a product":** 8 → 9 → 13.1 (Stripe) → 16
- **Integration-platform focus:** 10 → 11 → 12 → 13 → 15 → 16
- **AI-first:** 10 (API) → 14 (chatbot) → 8 (depth) → 16
- **Each phase stays runnable + tested** before the next (same discipline as 0–7).

## Cross-cutting reuse
Most future work extends what already exists:
- Webhooks/connectors → **Celery + `transaction.on_commit` + audit/event patterns** (Phases 4–5)
- API keys/scopes → **the permission-class + tenant-scoping model** (Phases 1–2)
- Notifications/real-time → **Redis** (already in stack)
- Billing quotas → **`Membership`/tenant model + middleware** hooks
