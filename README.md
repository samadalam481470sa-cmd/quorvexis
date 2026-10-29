# QUORVEXIS
### Cloud security command center · Full-stack monorepo

Quorvexis is an **early-stage enterprise security operations prototype**. It combines a Next.js command center with a FastAPI service, PostgreSQL organization-scoped domain models, MongoDB telemetry, Redis-backed authentication rate limiting, deterministic explainable risk scoring, and Docker-based local orchestration.

> **Status:** Initial engineering release. Not an audited security product. No customer integrations, live threat feeds, trained AI model, SSO, MFA, billing or production-ready database migrations are included yet. The UI shows only data explicitly created within the workspace.

## ⚠️ Current status — why the application may not run yet

**Development prototype · not a hosted or production-ready application.** This repository contains an initial full-stack implementation, but **a successful end-to-end Docker build, a live deployment, and passing GitHub Actions checks have not yet been confirmed**. The repository is **not** currently presented as a publicly accessible hosted service. A visitor to GitHub cannot simply click a website and start using it.

**What is implemented vs. what is not verified:**

| Area | Current state |
| --- | --- |
| Next.js frontend / FastAPI backend | Source code committed; successful full-stack startup **not yet verified** |
| PostgreSQL, MongoDB, Redis | Local Docker Compose services configured; require working Docker and local setup |
| Authentication, organization roles, dashboards | Initial implementation; production security review and integration verification pending |
| GitHub Actions | Workflow files added; **no passing result independently confirmed** as of October 29, 2026 |
| Public URL / cloud hosting | No completed public deployment supplied or verified |
| Real cloud connectors / AI threat model | **Not implemented**; event scoring is deterministic rules-based, not trained ML |
| Enterprise readiness | Not audited or suitable for protecting real customer infrastructure |

### Why it might not start on your machine

- **Environment configuration is mandatory.** Copy `.env.example` to `.env` and supply a **random** `JWT_SECRET` (at least 32 characters) and URL-safe `POSTGRES_PASSWORD`. The Compose file refuses to start without them.
- **Docker is required for the documented local workflow.** Install Docker Desktop / Docker Engine with Compose, then run `docker compose up --build` from the repository root. Build or runtime errors may still exist because the entire stack has not been validated end to end.
- **The UI is local, not deployed to the internet.** After a successful startup, open `http://localhost:3000` **on the machine running Docker**. The API and databases are intentionally private to the Compose network.
- **A fresh workspace has no telemetry.** Sign up and create an organization; the dashboard will initially be empty. Optional `DEMO_MODE=true` allows its owner to populate clearly labeled synthetic sample events.
- **Production functionality is unfinished.** There is no live SIEM/cloud connector, payment system, production infrastructure, MFA/SSO, or trained AI detection service.

### Troubleshooting and verification

```bash
# From the repository root, after configuring .env:
docker compose config                  # Validate Compose configuration
docker compose up --build              # Build and start local dependencies and services
docker compose ps                      # Inspect running containers
docker compose logs --tail=100 api web # Review errors in API/frontend
```

If startup fails, capture the error output from the failing container and check the [GitHub Actions runs](https://github.com/samadalam481470sa-cmd/quorvexis/actions). **A green CI run would validate its configured checks only, not production readiness.** This notice is intentionally conservative: it does **not** claim a specific build failure without logs proving one.

**For recruiters and contributors:** Quorvexis is a work-in-progress security-engineering portfolio / SaaS foundation, not yet a commercially deployable security platform. The roadmap below documents what remains.

## Features implemented

- Responsive dark-mode command center, organization registration and sign-in.
- Next.js server-side API gateway; HttpOnly SameSite=Strict session cookie. The JWT stays server-side rather than being stored in browser localStorage.
- FastAPI with access tokens (15-minute expiry), Argon2id passwords, bounded registration/login attempts, allowlisted proxy routes, input validation and baseline security headers.
- PostgreSQL for users, organizations, memberships, assets, incident records, and audit entries. All read/write queries scope by the principal's organization.
- MongoDB for time-series signal ingestion and 7-day dashboards, with indexed organization and timestamp.
- Redis for IP/account-scoped rate limits. Explainer-based event risk scoring with no opaque AI claims.
- Role-gated asset creation, incident creation/updates and event ingestion. Production mode disables demo seed route.
- Docker Compose for four internal services, automated Python tests, web type checking/build and CI.

## Local start

Requirements: Docker and Docker Compose.

1. Copy `.env.example` to `.env`.
2. Generate a unique JWT secret using `python -c "import secrets; print(secrets.token_urlsafe(48))"` and set `JWT_SECRET`.
3. Set `POSTGRES_PASSWORD` to a long URL-safe password. Keep `.env` out of Git.
4. Run `docker compose up --build`.
5. Open **http://localhost:3000**. Create a workspace with a strong password. If `DEMO_MODE=true`, the owner can load clearly labeled synthetic data.

The only port exposed is the local web UI on **127.0.0.1:3000**; databases and API remain on Docker's internal network.

## Architecture

```text
Browser (session cookie)
    |
Next.js frontend and same-origin BFF [apps/web]
    | Authorization: Bearer token (internal)
FastAPI [apps/api]
    |-- PostgreSQL: organizations, users, roles, assets, incidents, audit trail
    |-- MongoDB: indexed security signal records and trending
    |-- Redis: distributed login/registration rate limiting
```

API routes (via web gateway): `/me`, `/overview`, `/assets`, `/incidents`, `/incidents/:id`, `/signals`, and the optional `/demo/seed`. OpenAPI is available at `http://api:8000/docs` from within the private network in development.

## Access control

Viewer: read only. Analyst: read + event/asset/incident writes. Admin: analyst privileges. Owner: admin privileges + optional development-only seed. Authorization is enforced server-side; browser UI permissions are not a trust boundary. Organization identity is taken from the signed token and revalidated against memberships on every API request, not accepted as a user-supplied organization ID.

## Engineering limitations and production roadmap

This first release is a functional skeleton rather than a production deployment. Before commercial rollout: implement password-reset and email-verification flows, verified domains and invitations, passkeys/MFA, OIDC/SAML SSO, session rotation and revocation, managed TLS ingress and WAF, trusted proxy configuration, Alembic migrations, database encryption/authentication and private network segmentation, secrets manager, telemetry retention/TTL, OpenTelemetry, backup restoration tests, SIEM ingestion connectors, multi-tenant integration tests, reliable event queues, SBOM/dependency scanning, security audit, legal/privacy review, billing, and SLOs. The development Compose databases have no internal authentication and **must not be exposed to public networks**.

The risk engine is rules-based and explainable, not a trained machine-learning system. Analytics reflect user-provided or synthetic signals, not a live security feed.

## Testing

```bash
python -m pip install -r apps/api/requirements.txt
PYTHONPATH=apps/api JWT_SECRET=testing-only-secret-not-for-production-use pytest apps/api/tests
cd apps/web && npm install && npm run lint && npm run build
```

## License

MIT; see [LICENSE](LICENSE).
