# Postman collection (Phases 0–4)

A single, self-contained collection — no environment file needed. It sends the
tenant subdomain as a `Host` header automatically, so it works against
`http://localhost:8000` without editing your hosts file.

## Import
In Postman: **Import** → `multi-tenant-crm.postman_collection.json`.
All variables (`baseUrl`, `tenant`, `email`, `password`, tokens, ids) live on the
collection itself — edit them under the collection's **Variables** tab.

## Use
1. Start the API and seed data:
   ```bash
   docker compose up -d
   docker compose run --rm web python manage.py seed_tenants
   ```
2. Run **Auth → Login** (stores `access_token`/`refresh_token` for all requests).
3. Suggested order to auto-populate ids:
   **List stages → Create lead → Create deal → Move deal → List activity**.

## Switching tenants
Edit the collection variable `tenant` (`acme` or `globex`) and update `email`
accordingly, then re-run **Login**. The same `access_token` used against the other
tenant returns **403** — that's the isolation guarantee.

## Demo users (password `password123`)
`owner@`, `admin@`, `manager@`, `sales_rep@`, `viewer@` for both
`acme.crm.local` and `globex.crm.local`.

## RBAC
Each request notes its minimum role. Log in as a lower role (e.g.
`viewer@acme.crm.local`) and watch writes return **403**.

## Note
If your Postman build refuses to send a custom `Host` header, add
`127.0.0.1 acme.crm.local globex.crm.local crm.local` to your hosts file and set
`baseUrl` to `http://{{tenant}}.crm.local:8000`.
