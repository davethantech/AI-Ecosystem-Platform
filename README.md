# AI Ecosystem Platform

A multi-tenant starter platform for hosted and self-hosted AI, designed for Docker deployment on a VPS. The repository is explicit about what works today versus future integrations.

## Included now

- Organization/workspace creation during registration; organization-scoped resource queries.
- Password hashing (Argon2 through pwdlib), signed JWT access tokens and token expiry.
- PostgreSQL in Docker Compose; SQLite supported for local backend development.
- Organization-scoped AI agent definition CRUD.
- Shared provider adapter for OpenAI-compatible chat completions and Ollama `/api/chat`.
- Chat history stored in PostgreSQL plus organization-scoped audit events.
- React/Vite web dashboard, model playground, agent manager, provider configuration guidance and audit table.
- Basic security headers, CORS allowlist, non-root API container, database health check and smoke tests.

## Not yet implemented

- Document upload/parsing, embeddings, vector database, and RAG citations.
- Agent tool execution, autonomous multi-agent coordination, durable workflow engine, scheduling and human approval gates.
- Organization invitations, complete role/member management UI, MFA, SSO, API keys, billing, per-tenant quotas/rate limiting and admin console.
- Model registry, fine-tuning jobs, evaluation suites, distributed workers, comprehensive observability and compliance certifications.
- Automated database migrations. Initial tables are created at API startup; use Alembic before production schema evolution.

## Local development

Requirements: Python 3.12+, Node.js 22+, npm.

Backend:

```bash
cd backend
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./ai_ecosystem.db
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api`, `/docs` and `/openapi.json` to `http://localhost:8000`.

## VPS deployment (Docker Compose)

1. Install Docker Engine and Docker Compose plugin on Ubuntu 22.04/24.04.
2. Clone this repository to the VPS.
3. Configure secrets:

```bash
cp .env.example .env
chmod 600 .env
./scripts/generate-secrets.sh
```

Insert unique generated values into `.env`. Ensure `POSTGRES_PASSWORD` contains only URL-safe alphanumeric characters; it is used in the container DATABASE_URL. Do not commit `.env`.

4. Set `OPENAI_API_KEY` if using hosted inference. For Ollama, install Ollama on the host, pull a model (for example `ollama pull llama3.2`) and keep it accessible only on a trusted network. Adjust `OLLAMA_BASE_URL` as needed.
5. Set `CORS_ORIGINS` to your actual website origin without a trailing slash, e.g. `https://ai.example.com`.
6. Build and start:

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 api web
curl -fsS http://127.0.0.1:8080/api/health
```

7. Point DNS to your VPS and proxy HTTPS to port 8080 using your existing Nginx/Let's Encrypt setup. Do not expose PostgreSQL or API port 8000 publicly. If Nginx runs on the host, bind web to `127.0.0.1:8080:80` and proxy to it.
8. After TLS is enabled, update `CORS_ORIGINS` in `.env` to the HTTPS origin and run `docker compose up -d`.

## Backups and tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Back up PostgreSQL regularly and test restore procedures. Configure encrypted off-server backups and log rotation before production use.

## API endpoints

- `GET /api/health`
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/organization`, `GET /api/dashboard`
- `GET/POST /api/agents`, `PUT/DELETE /api/agents/{id}`
- `POST /api/chat`, `GET /api/conversations`
- `GET /api/audit`

## Security notes

This is a starter implementation, not a security certification. Before onboarding paying customers, add Alembic migrations, request/login throttling, stronger abuse protection, MFA/SSO as needed, full membership and RBAC management, a review of browser token storage, secrets manager integration, backup/restore drills, dependency scanning and security testing. JWTs are stored in browser localStorage in this initial UI; consider secure HttpOnly cookies and CSRF protection for a higher-assurance production deployment.
