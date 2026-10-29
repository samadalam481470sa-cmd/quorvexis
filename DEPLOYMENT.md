# Quorvexis deployment guide

## Public interactive showcase

**Production alias:** [https://quorvexis-demo.vercel.app](https://quorvexis-demo.vercel.app)

- **Vercel deployment:** `dpl_C9uDcYQ1bVGLN9k5ijsbNZv2J87i`, status **READY** on October 29, 2026.
- **Source:** [showcase/index.html](showcase/index.html) plus [showcase/images](showcase/images), committed to the repository alongside the README preview assets.
- **Scope:** standalone static HTML and SVG product previews. Tab switching and sample incident triage use browser-only JavaScript state. **No real authentication, API, database, user accounts, or cloud connectors are hosted at this URL.**
- **Verification:** Vercel reports READY and lists the uploaded source files. An independent external HTTP request was not successful through the available inspection environment, so public reachability has not been separately confirmed.
- **Maintenance:** This static showcase was deployed through Vercel's source-file API. It is **not automatically deployed on GitHub pushes**. Updating `showcase/` in GitHub does not update Vercel until a new deployment is initiated.

### Why the main full-stack application isn't at the showcase URL

The monorepo's `apps/web` Next.js application expects the separate FastAPI backend and PostgreSQL, MongoDB, Redis. Those services have not been deployed as a secure production stack. The standalone `/demo` page under `apps/web/app/demo/page.tsx` can be run locally, but the Vercel site is a different static preview built to share the project's direction without exposing any backend.

## Local full-stack environment

1. Install Docker with the Compose plugin.
2. Copy `.env.example` to `.env`.
3. Generate a random `JWT_SECRET` and configure `POSTGRES_PASSWORD`.
4. Run `docker compose up --build`.
5. Visit `http://localhost:3000` to register your local workspace, or visit `http://localhost:3000/demo` for the standalone Next.js synthetic demo.

The GitHub Actions checks cover Python tests, frontend type checking/build, and Compose config validation; they **do not yet verify a live, fully integrated container deployment**.

## Future full-stack hosting

To deploy the real application, first configure managed PostgreSQL/MongoDB/Redis, authenticated private networks, migration automation, rotated production secrets, TLS, backup/restore tests, secure OIDC/MFA, audit retention, multi-tenant integration tests, and monitoring. Do not expose the development Compose databases on the public internet.

The Vercel GitHub integration could not be linked from this environment because the provider rejected it with a GitHub-integration-not-installed error. To enable source-driven auto-deploys, install the GitHub app in Vercel with access to the Quorvexis repo; select `apps/web` as the project root. That separate effort will still require a secured public-facing API environment.
