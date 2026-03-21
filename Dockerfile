FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

COPY pyproject.toml README.md ./
COPY prompts ./prompts
COPY src ./src
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN python -m pip install --no-cache-dir .

EXPOSE 10000

CMD ["python", "-m", "cybersentinel.web_server"]
