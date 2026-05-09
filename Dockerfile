FROM node:22-alpine AS frontend-builder

WORKDIR /app

COPY package.json package-lock.json vite.config.js ./
COPY frontend ./frontend

RUN npm ci
RUN npm run build


FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY --from=frontend-builder /app/app/static/spa ./app/static/spa

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
