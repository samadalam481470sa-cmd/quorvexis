# Deployment and demonstration

## Interactive preview

The route `/demo` is a **standalone interactive product preview** that uses bundled, synthetic sample data and does not require login, API, or databases. It is intended for portfolio and evaluation purposes, **not** as a real threat-monitoring service. None of the values are live.

## Local complete stack

Follow [README.md](README.md) and configure `.env`, then run `docker compose up --build`. This requires a working Docker environment and has not been certified in CI end-to-end.

## Hosting architecture

The Next.js application can be hosted separately, but authentication and live dashboard data require a reachable FastAPI service, Postgres, MongoDB and Redis. The UI's `API_INTERNAL_URL` points to the FastAPI backend. This is a **server-side** URL; never point it to an unprotected public development endpoint.

To host the frontend on Vercel: connect the repository in the Vercel dashboard (the Vercel GitHub integration must be installed), set root directory to `apps/web`, framework to Next.js, and configure the API URL for the server runtime. Do **not** publish the current development Compose databases to the internet. Deploy a properly secured backend, secrets, TLS, database authentication, migrations and network controls before turning on real user registration or production accounts.

### Current deployment blocker

Automated deployment from this connected workspace was attempted on October 29, 2026. Vercel rejected the GitHub repository link with **HTTP 400**: *"To link a GitHub repository, you need to install the GitHub integration first."* No working Vercel URL was obtained. This is an integration/authorization blocker, not proof that the application itself compiles.

For a preview, connect GitHub to Vercel, then redeploy. Check GitHub Actions for the latest build statuses; the CI check results are not independently confirmed.
