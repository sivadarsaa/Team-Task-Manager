# S and Groups

Production-ready full-stack task management app with:

- FastAPI backend
- React + Vite frontend
- PostgreSQL support
- Railway-ready deployment
- Vercel-ready standalone frontend deployment

The backend can serve the built SPA, and the frontend can also be deployed separately to any Vite-compatible static host.

## Stack

- FastAPI
- SQLAlchemy
- PostgreSQL / SQLite
- React
- Vite
- Railway

## Project Structure

```text
app/                  FastAPI app
frontend/             React source
Dockerfile            Railway/container deployment
railway.toml          Railway config
vite.config.js        Embedded + standalone frontend builds
requirements.txt      Python production dependencies
package.json          Frontend build scripts
vercel.json           Vercel SPA deployment config
```

## Environment Variables

Copy `.env.example` to `.env` for local development.

### Backend

```env
APP_NAME=S and Groups
ENVIRONMENT=development
SECRET_KEY=replace-with-a-long-random-secret-at-least-32-characters
DATABASE_URL=sqlite:///C:/Users/your-user/AppData/Local/TeamTaskManager/team_task_manager.db
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SECURE_COOKIES=false
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
DEMO_PASSWORD=ChangeThisDemoPassword123!
```

### Frontend

```env
VITE_API_BASE_URL=
VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000
```

Notes:

- `SECRET_KEY` is required and must be a real long secret.
- For separate frontend/backend production deployments on Vercel + Railway, set:
  - `SECURE_COOKIES=true`
  - `COOKIE_SAMESITE=none`
  - `FRONTEND_URL=https://your-frontend-domain`
  - `CORS_ORIGINS=https://your-frontend-domain`
  - `VITE_API_BASE_URL=https://your-backend-domain`
- `VITE_*` variables are public build-time variables. Never put secrets in them.

## Local Development

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend

```bash
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/health` to `VITE_DEV_PROXY_TARGET` when `VITE_API_BASE_URL` is empty.

## Useful Scripts

```bash
npm run dev
npm run build
npm run build:frontend
npm run preview
npm run check
python app/seed.py
```

What they do:

- `npm run build`: builds the SPA for backend-served deployment into `app/static/spa`
- `npm run build:frontend`: builds a standalone static frontend into `frontend/dist`
- `npm run check`: verifies both production build modes

## GitHub Push Checklist

1. Initialize or connect your Git repository.
2. Confirm `.env` is not staged.
3. Confirm local databases, `node_modules`, and build output are ignored.
4. Push the repo to GitHub.

Files already ignored for safe pushes:

- `.env`
- `node_modules/`
- `frontend/dist/`
- `app/static/spa/`
- `*.db`
- `data/`

## Railway Backend Deployment

This repo includes a root `Dockerfile`, so Railway can build the backend consistently without relying on mixed-language auto-detection.
`railway.toml` already points Railway at the Dockerfile builder and uses `/health` as the deployment healthcheck.

### Steps

1. Push the repository to GitHub.
2. In Railway, create a new project from the GitHub repo.
3. Add a PostgreSQL service in Railway.
4. Set backend variables in the Railway service:

```env
ENVIRONMENT=production
APP_NAME=S and Groups
SECRET_KEY=your-long-random-production-secret
DATABASE_URL=${{Postgres.DATABASE_URL}}
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SECURE_COOKIES=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
FRONTEND_URL=https://your-frontend-domain
CORS_ORIGINS=https://your-frontend-domain
DEMO_PASSWORD=ChangeThisDemoPassword123!
```

5. Deploy.
6. Verify the backend with `/health`.

### Railway Notes

- `railway.toml` sets the service healthcheck.
- Railway will automatically detect the backend correctly because `railway.toml` forces the `DOCKERFILE` builder.
- The Docker build runs the embedded frontend build automatically.
- The Docker `CMD` now honors Railway's injected `PORT` variable.
- The backend will fail fast on startup if production cookie settings are unsafe.
- The production startup command is:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips "*"
```

### Exact Railway Variables

Use these exact keys in the Railway backend service:

```env
APP_NAME=S and Groups
ENVIRONMENT=production
SECRET_KEY=generate-a-random-secret-at-least-32-characters
DATABASE_URL=${{Postgres.DATABASE_URL}}
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SECURE_COOKIES=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
CORS_ORIGINS=https://your-frontend.vercel.app
FRONTEND_URL=https://your-frontend.vercel.app
DEMO_PASSWORD=ChangeThisDemoPassword123!
```

If you decide to serve the SPA from Railway only, you can switch `COOKIE_SAMESITE` back to `lax` and leave `CORS_ORIGINS` empty.

## Frontend Deployment

The frontend can be deployed separately to Vercel as a static Vite app.

### Vercel Settings

```env
Framework Preset=Vite
Build Command=npm run build:frontend
Output Directory=frontend/dist
Install Command=npm install
```

`vercel.json` already adds the required SPA rewrite so React Router deep links work in production.

### Required frontend variable

```env
VITE_API_BASE_URL=https://your-backend-domain
```

### Exact Vercel Variables

```env
VITE_API_BASE_URL=https://your-backend.up.railway.app
```

### Build command

```bash
npm run build:frontend
```

### Publish directory

```text
frontend/dist
```

### Typical Vercel setup

- Root directory: repository root
- Build command: `npm run build:frontend`
- Output directory: `frontend/dist`
- Environment variable: `VITE_API_BASE_URL=https://your-backend-domain`

Per Vite's deployment guidance, `vite preview` is only for local previewing, not production hosting.

## PostgreSQL Notes

- Railway Postgres URLs are accepted directly.
- `postgres://` and `postgresql://` URLs are normalized to `postgresql+psycopg://`.
- Production connections use SQLAlchemy connection health checks with `pool_pre_ping=True`.
- SQLite is still supported for local development.

## Production Readiness Notes

This repo is prepared for production deployment with:

- environment-based backend and frontend configuration
- no hardcoded runtime secrets
- cookie settings configurable for same-origin or cross-origin deployment
- CORS configured from env vars
- embedded and standalone frontend build modes
- lazy-loaded heavy frontend charts and kanban code paths
- Docker-based Railway compatibility
- Vercel SPA rewrite support for React Router deep links
- production-safe startup command
- local-only files excluded from source control
- secure cross-origin cookie configuration for Railway backend + Vercel frontend

## Step-By-Step Deployment

1. Push the latest repo changes to GitHub.
2. In Vercel, create the frontend project from this repo so you know the production frontend domain you want to use.
3. In Railway, create the backend service from the same repo and add a PostgreSQL service.
4. In Railway, add the backend variables listed in `Exact Railway Variables`, using your chosen Vercel production URL for both `FRONTEND_URL` and `CORS_ORIGINS`.
5. Deploy Railway and wait for `/health` to return `200`.
6. Copy the public Railway backend URL, for example `https://your-backend.up.railway.app`.
7. In Vercel, set `VITE_API_BASE_URL` to that Railway backend URL.
8. In Vercel, deploy the frontend using the existing `vercel.json` config.
9. Open the Vercel production URL and test signup, login, project creation, member assignment, task movement, dashboard charts, and analytics.
10. If your final Vercel production URL differs from the one you put into Railway, update `FRONTEND_URL` and `CORS_ORIGINS` in Railway and redeploy once more.

## End-To-End Verification

Local verification completed before deployment:

- `npm run check` passed for both backend-embedded and standalone frontend builds.
- Production config validation passed with secure cookies and explicit frontend origins.
- A full backend smoke test passed for auth, logout/login, RBAC, project creation, member assignment, task creation, task status updates, dashboard, analytics, and `/health`.

One backend runtime bug was fixed during verification: task status updates now coerce enum values correctly before activity logging, which prevents production failures during Kanban moves.

## Final Verification

Before shipping, run:

```bash
npm run check
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then verify:

- backend health endpoint works
- login/signup works
- project/task/member flows work
- manager/member role boundaries still behave correctly
- dashboard and analytics still load after task changes
- frontend can call the deployed backend using `VITE_API_BASE_URL`
