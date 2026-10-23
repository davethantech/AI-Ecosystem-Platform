# AI Ecosystem Platform

Multi-tenant AI workspace starter for hosted and self-hosted model providers, built for VPS deployment.

## Features in this starter

- React + Vite dashboard
- FastAPI backend
- PostgreSQL with Docker Compose
- Registration, login, JWT authentication, tenant-scoped resources
- AI agent definitions and chat history
- OpenAI-compatible hosted model adapter and Ollama adapter
- Audit events, health endpoint, initial tests

## Planned integrations

Document ingestion and RAG, vector search, autonomous multi-agent execution, visual workflows, billing, MFA/SSO, formal quotas/rate limits, model registry, fine-tuning and distributed workers are not fully implemented in this starter. Review the project documentation before treating this as production-ready.

## Quick start

1. Copy `.env.example` to `.env` and replace all example secrets.
2. Configure a hosted provider key or a reachable Ollama service if you want to use AI chat.
3. Run `docker compose up -d --build`.
4. Check `curl http://127.0.0.1:8080/api/health`.

Do not expose PostgreSQL or the backend port publicly. Put the web service behind HTTPS on your VPS. Never commit `.env` or provider secrets.
