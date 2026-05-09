# S and Groups

Production-ready full-stack task management app with:

- FastAPI backend
- React + Vite frontend
- PostgreSQL support
- Railway-ready deployment

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
- For separate frontend/backend production deployments, set:
  - `SECURE_COOKIES=true`
  - `COOKIE_SAMESITE=none`
  - `FRONTEND_URL=https://your-frontend-domain`
  - `CORS_ORIGINS=https://your-frontend-domain`
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
SECURE_COOKIES=true
COOKIE_SAMESITE=lax
```

If the frontend is deployed on a different domain, use:

```env
COOKIE_SAMESITE=none
FRONTEND_URL=https://your-frontend-domain
CORS_ORIGINS=https://your-frontend-domain
```

5. Deploy.
6. Verify the backend with `/health`.

### Railway Notes

- `railway.toml` sets the service healthcheck.
- The Docker build runs the embedded frontend build automatically.
- The production startup command is:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips "*"
```

## Frontend Deployment

The frontend can be deployed separately to any Vite-compatible static host.

### Required frontend variable

```env
VITE_API_BASE_URL=https://your-backend-domain
```

### Build command

```bash
npm run build:frontend
```

### Publish directory

```text
frontend/dist
```

### Typical static-host setup

- Build command: `npm run build:frontend`
- Publish directory: `frontend/dist`
- Environment variable: `VITE_API_BASE_URL=https://your-backend-domain`

Per Vite’s deployment guidance, `vite preview` is only for local previewing, not production hosting.

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
- production-safe startup command
- local-only files excluded from source control

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
- frontend can call the deployed backend using `VITE_API_BASE_URL`
