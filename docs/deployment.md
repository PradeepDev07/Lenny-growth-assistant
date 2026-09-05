# Deployment Guide — Lenny Growth Assistant

This document outlines how to deploy the **Lenny Growth Assistant** to production environments with high availability, security, and automated SSL.

---

## Architecture Topology

```
                   Internet / Users
                          │
                   HTTPS (Port 443)
                          ▼
        ┌───────────────────────────────────┐
        │  Reverse Proxy / CDN              │
        │  (Caddy / Nginx / Vercel Edge)    │
        └─────────────────┬─────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
    Route: /*                       Route: /api/* (via BFF)
          │                               │
          ▼                               ▼
┌───────────────────┐           ┌───────────────────┐
│ Next.js Frontend  │  HTTP     │  FastAPI Backend  │
│ (Port 3000)       ├──────────►│  (Port 8000)      │
│ Node.js Standalone│           │  Python 3.12      │
└───────────────────┘           └─────────┬─────────┘
                                          │
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
             ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
             │  PostgreSQL  │     │ Vector Store │     │  Cloud LLMs  │
             │  (Sessions & │     │ (BM25 Cache) │     │ (Gemini /    │
             │   Messages)  │     │              │     │  OpenRouter) │
             └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Architectural Notes
1. **Frontend BFF (Backend For Frontend)**: The Next.js client browser only calls `/api/*`. The Next.js server proxies these requests internally to the FastAPI backend at `FASTAPI_URL`. The FastAPI backend **does not need to be exposed directly to the public internet** in containerized environments.
2. **Streaming Support (SSE)**: The chat endpoint streams server-sent events (`text/event-stream`). Any reverse proxy or load balancer in front must have response buffering disabled (or stream buffering set to off).
3. **Database Auto-Migration**: Tables (`sessions`, `messages`, `artifacts`) are automatically initialized on startup via SQLAlchemy `lifespan`.

---

## Environment Variables Reference

| Variable | Description | Default | Required in Production |
|---|---|---|---|
| `ENVIRONMENT` | Environment name (`production` or `development`) | `development` | Yes (`production`) |
| `DATABASE_URL` | PostgreSQL connection URI | `sqlite:///./growth_assistant.db` | Yes |
| `GEMINI_API_KEY` | Google AI Studio API Key | None | Yes (or OpenRouter) |
| `OPENROUTER_API_KEY` | OpenRouter API Key | None | Optional (recommended) |
| `FASTAPI_URL` | URL used by Next.js server to reach FastAPI | `http://127.0.0.1:8000` | Yes |
| `NEXT_PUBLIC_API_URL` | Base API route for the browser | `/api` | No |
| `CORS_ORIGINS` | Comma-separated or JSON list of allowed origins | `http://localhost:3000,...` | When direct API calls are made |
| `DOMAIN_NAME` | Production domain name for Caddy auto-SSL | `localhost` | For Docker + Caddy setup |
| `ACME_EMAIL` | Contact email for Let's Encrypt certificates | `admin@example.com` | For Docker + Caddy setup |

---

## Strategy A: Single VM / VPS Deployment (Docker Compose + Caddy)

*Best for: DigitalOcean Droplet ($12-24/mo), Hetzner Cloud, AWS EC2 (t3.small/medium), Linode.*

This approach runs Caddy (with automatic Let's Encrypt SSL), Next.js (standalone container), FastAPI, and PostgreSQL with private internal networking.

### Step 1: Provision Server & Install Docker
```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y curl git
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### Step 2: Clone Codebase & Configure Secrets
```bash
git clone https://github.com/PradeepDev07/Lenny-growth-assistant.git
cd Lenny-growth-assistant

# Create production environment file
cat << 'ENV' > .env
ENVIRONMENT=production
DEBUG=false

# Domain & SSL
DOMAIN_NAME=growth.yourdomain.com
ACME_EMAIL=your-email@example.com

# Database credentials
POSTGRES_USER=lenny_prod
POSTGRES_PASSWORD=generate_a_strong_random_password_here
POSTGRES_DB=growth_assistant

# LLM Providers
GEMINI_API_KEY=AIzaSy...
OPENROUTER_API_KEY=sk-or-v1-...

# Frontend configuration
FASTAPI_URL=http://backend:8000
NEXT_PUBLIC_API_URL=/api
CORS_ORIGINS=*
ENV
```

### Step 3: Point DNS Record
Add an **A Record** in your DNS provider pointing `growth.yourdomain.com` to your server's Public IP address.

### Step 4: Launch Production Stack
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 5: Verify Health
```bash
# Check running containers
docker compose -f docker-compose.prod.yml ps

# Check backend health
curl -f http://localhost:8000/health

# View live logs
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## Strategy B: Managed Cloud PaaS (Recommended for Zero-DevOps)

*Best for: Instant global deployments, zero server maintenance, automatic scaling.*

- **Frontend**: [Vercel](https://vercel.com)
- **Backend**: [Render](https://render.com) or [Railway](https://railway.app)
- **Database**: [Supabase](https://supabase.com) or [Neon](https://neon.tech) (PostgreSQL)

### 1. Database (Neon / Supabase)
1. Create a free PostgreSQL project on Neon or Supabase.
2. Copy the connection string URI (e.g. `postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require`).

### 2. Backend (Render / Railway)
1. Create a new **Web Service** pointing to your GitHub repository.
2. Set **Root Directory** to repository root.
3. Choose **Docker** as environment (Render will automatically detect `backend/Dockerfile` if configured or specify Dockerfile path `backend/Dockerfile`).
4. Set Environment Variables:
   - `ENVIRONMENT` = `production`
   - `DATABASE_URL` = `<your_neon_or_supabase_postgres_url>`
   - `GEMINI_API_KEY` = `<your_gemini_api_key>`
   - `OPENROUTER_API_KEY` = `<your_openrouter_api_key>`
   - `CORS_ORIGINS` = `https://<your-vercel-app>.vercel.app,https://<your-custom-domain>.com`
5. Set Health Check Path: `/health`.
6. Deploy. Note your backend URL (e.g. `https://lenny-backend.onrender.com`).

### 3. Frontend (Vercel)
1. Import your GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Set Environment Variables:
   - `FASTAPI_URL` = `https://lenny-backend.onrender.com` (your backend URL)
   - `NEXT_PUBLIC_API_URL` = `/api`
4. Deploy. Vercel automatically deploys the Next.js App Router and provisions SSL.

---

## Strategy C: Enterprise Containers (AWS ECS / GCP Cloud Run)

### Backend on GCP Cloud Run
1. Build and push image:
   ```bash
   gcloud builds submit --tag gcr.io/[PROJECT_ID]/lenny-backend -f backend/Dockerfile .
   ```
2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy lenny-backend \
     --image gcr.io/[PROJECT_ID]/lenny-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars ENVIRONMENT=production,DATABASE_URL=[DB_URI],GEMINI_API_KEY=[KEY]
   ```

---

## Pre-flight Checklist

- [ ] **Secrets**: Ensure `.env` is **never** committed to Git (`.gitignore` excludes it).
- [ ] **Docker Context**: `.dockerignore` prevents uploading `node_modules`, `.venv`, `.next`, and cache files.
- [ ] **Streaming Compatibility**: When using Nginx/Cloudflare, verify that response buffering is disabled for `/api/chat` (`proxy_buffering off;`) to allow smooth token streaming.
- [ ] **Database Persistence**: Ensure PostgreSQL uses a persistent volume or managed cloud instance so user sessions survive container updates.
- [ ] **Health Probe**: Verify that `GET /health` returns status `200` with `"db": true`.
